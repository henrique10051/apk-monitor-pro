"""
NetworkIncidentDetector - Detecção e análise de incidentes de rede
Integra com ADBManager para captura inteligente de erros de rede
"""

import re
import json
from datetime import datetime, timedelta
from collections import deque
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum


class ErrorCategory(Enum):
    SSL_TLS        = "SSL/TLS"
    TIMEOUT        = "Timeout"
    DNS            = "DNS"
    CONNECTION     = "Conexão"
    HTTP           = "HTTP"
    CERTIFICATE    = "Certificado"
    CLEARTEXT      = "Tráfego HTTP bloqueado"
    SOCKET         = "Socket"
    UNKNOWN        = "Desconhecido"


@dataclass
class NetworkIncident:
    timestamp: datetime
    category: ErrorCategory
    trigger_line: str
    context_before: List[str]     # N linhas antes do erro
    context_after: List[str]      # N linhas após o erro (preenchido depois)
    raw_exception: Optional[str]  = None
    endpoint: Optional[str]       = None
    http_code: Optional[int]      = None
    interval_from_last: Optional[float] = None  # segundos desde o último erro
    
    def to_dict(self):
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        d['category']  = self.category.value
        return d
    
    def summary(self) -> str:
        ts = self.timestamp.strftime("%H:%M:%S.%f")[:-3]
        ep = f" → {self.endpoint}" if self.endpoint else ""
        code = f" [{self.http_code}]" if self.http_code else ""
        return f"[{ts}] {self.category.value}{code}{ep}"


# ---------------------------------------------------------------------------
# Padrões de detecção
# ---------------------------------------------------------------------------

NETWORK_ERROR_PATTERNS: List[Tuple[ErrorCategory, str]] = [
    # SSL / TLS
    (ErrorCategory.SSL_TLS,       r"javax\.net\.ssl\.SSLException"),
    (ErrorCategory.SSL_TLS,       r"javax\.net\.ssl\.SSLHandshakeException"),
    (ErrorCategory.SSL_TLS,       r"ssl\.SSLPeerUnverifiedException"),
    (ErrorCategory.SSL_TLS,       r"SSLProtocolException"),
    (ErrorCategory.SSL_TLS,       r"Handshake failed"),
    # Certificado / pinning
    (ErrorCategory.CERTIFICATE,   r"CertPathValidatorException"),
    (ErrorCategory.CERTIFICATE,   r"Trust anchor for certification path not found"),
    (ErrorCategory.CERTIFICATE,   r"certificate.*expired"),
    (ErrorCategory.CERTIFICATE,   r"CERTIFICATE_VERIFY_FAILED"),
    (ErrorCategory.CERTIFICATE,   r"Certificate pinning failure"),
    (ErrorCategory.CERTIFICATE,   r"CertificateException"),
    # DNS
    (ErrorCategory.DNS,           r"UnknownHostException"),
    (ErrorCategory.DNS,           r"Unable to resolve host"),
    (ErrorCategory.DNS,           r"No address associated with hostname"),
    # Timeout
    (ErrorCategory.TIMEOUT,       r"SocketTimeoutException"),
    (ErrorCategory.TIMEOUT,       r"connect timed out"),
    (ErrorCategory.TIMEOUT,       r"Read timed out"),
    (ErrorCategory.TIMEOUT,       r"timeout"),
    # Conexão recusada / reset
    (ErrorCategory.CONNECTION,    r"ConnectException"),
    (ErrorCategory.CONNECTION,    r"Connection refused"),
    (ErrorCategory.CONNECTION,    r"Connection reset"),
    (ErrorCategory.CONNECTION,    r"ECONNREFUSED"),
    (ErrorCategory.CONNECTION,    r"ECONNRESET"),
    (ErrorCategory.CONNECTION,    r"Failed to connect"),
    (ErrorCategory.CONNECTION,    r"NetworkOnMainThreadException"),
    # HTTP status errors
    (ErrorCategory.HTTP,          r"HTTP 4\d\d"),
    (ErrorCategory.HTTP,          r"HTTP 5\d\d"),
    (ErrorCategory.HTTP,          r"Unexpected response code \d+"),
    (ErrorCategory.HTTP,          r"Response\.error\(\)"),
    # Cleartext (HTTP em vez de HTTPS)
    (ErrorCategory.CLEARTEXT,     r"CLEARTEXT communication.*not permitted"),
    (ErrorCategory.CLEARTEXT,     r"usesCleartextTraffic"),
    # Socket genérico
    (ErrorCategory.SOCKET,        r"SocketException"),
    (ErrorCategory.SOCKET,        r"java\.net\.Socket"),
    (ErrorCategory.SOCKET,        r"broken pipe"),
    (ErrorCategory.SOCKET,        r"EPIPE"),
]

# Regex para extrair endpoint/URL da linha de log
URL_PATTERN      = re.compile(r'https?://[^\s\'"<>]+')
HTTP_CODE_PATTERN = re.compile(r'\b([45]\d{2})\b')

# Tags de bibliotecas HTTP — usadas para filtro extra no logcat
HTTP_TAGS = [
    "OkHttp", "okhttp3", "Retrofit", "Volley",
    "HttpURLConnection", "SSLSocketFactory",
    "NetworkSecurityConfig", "SSLHandshake",
    "ConnectException", "CertPathValidator",
    "SSLPeerUnverified",
]


# ---------------------------------------------------------------------------
# Detector principal
# ---------------------------------------------------------------------------

class NetworkIncidentDetector:
    """
    Processa linhas de logcat em stream e detecta incidentes de rede.
    Mantém janela deslizante de contexto para cada incidente.
    """

    def __init__(self, context_before: int = 25, context_after: int = 10):
        self.context_before = context_before
        self.context_after  = context_after

        self._buffer: deque = deque(maxlen=context_before)
        self._incidents: List[NetworkIncident] = []
        self._pending_after: List[Tuple[NetworkIncident, list, int]] = []
        # ^-- (incident, after_lines_list, remaining_count)

        self._compiled = [
            (cat, re.compile(pat, re.IGNORECASE))
            for cat, pat in NETWORK_ERROR_PATTERNS
        ]

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def feed(self, line: str) -> Optional[NetworkIncident]:
        """
        Alimenta uma linha de log.
        Retorna NetworkIncident se essa linha disparou detecção, senão None.
        """
        # Alimenta linhas de contexto "after" para incidentes pendentes
        for item in list(self._pending_after):
            inc, after_lines, remaining = item
            after_lines.append(line)
            item_idx = self._pending_after.index(item)
            self._pending_after[item_idx] = (inc, after_lines, remaining - 1)
            if remaining - 1 <= 0:
                self._pending_after.remove(self._pending_after[item_idx])

        self._buffer.append(line)

        matched_cat = self._match(line)
        if matched_cat is None:
            return None

        incident = self._build_incident(line, matched_cat)
        self._incidents.append(incident)

        # Inicia coleta de contexto after
        after_lines: list = []
        incident.context_after = after_lines          # referência compartilhada
        self._pending_after.append((incident, after_lines, self.context_after))

        return incident

    @property
    def incidents(self) -> List[NetworkIncident]:
        return list(self._incidents)

    @property
    def count(self) -> int:
        return len(self._incidents)

    def analyze(self) -> Dict:
        """
        Retorna análise consolidada dos incidentes coletados.
        """
        if not self._incidents:
            return {"total": 0, "categories": {}, "intervals": [], "pattern": None, "most_likely_cause": None}

        cats: Dict[str, int] = {}
        for inc in self._incidents:
            cats[inc.category.value] = cats.get(inc.category.value, 0) + 1

        intervals = [
            inc.interval_from_last
            for inc in self._incidents
            if inc.interval_from_last is not None
        ]

        avg_interval = sum(intervals) / len(intervals) if intervals else None
        pattern      = self._detect_pattern(intervals)
        cause        = self._most_likely_cause(cats, pattern, avg_interval)

        return {
            "total": self.count,
            "categories": cats,
            "intervals": [round(i, 1) for i in intervals],
            "avg_interval_seconds": round(avg_interval, 1) if avg_interval else None,
            "pattern": pattern,
            "most_likely_cause": cause,
            "endpoints": list({inc.endpoint for inc in self._incidents if inc.endpoint}),
            "first_at": self._incidents[0].timestamp.isoformat(),
            "last_at": self._incidents[-1].timestamp.isoformat(),
        }

    def export_report(self, path: str = "network_incidents.json"):
        """Exporta todos os incidentes para JSON."""
        data = {
            "generated_at": datetime.now().isoformat(),
            "analysis": self.analyze(),
            "incidents": [inc.to_dict() for inc in self._incidents],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    def clear(self):
        self._incidents.clear()
        self._buffer.clear()
        self._pending_after.clear()

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _match(self, line: str) -> Optional[ErrorCategory]:
        for cat, pattern in self._compiled:
            if pattern.search(line):
                return cat
        return None

    def _build_incident(self, line: str, category: ErrorCategory) -> NetworkIncident:
        endpoint  = self._extract_url(line) or self._extract_url_from_buffer()
        http_code = self._extract_http_code(line)

        interval = None
        if self._incidents:
            delta = datetime.now() - self._incidents[-1].timestamp
            interval = delta.total_seconds()

        return NetworkIncident(
            timestamp=datetime.now(),
            category=category,
            trigger_line=line.strip(),
            context_before=list(self._buffer)[:-1],   # sem a linha atual
            context_after=[],
            raw_exception=self._extract_exception(line),
            endpoint=endpoint,
            http_code=http_code,
            interval_from_last=interval,
        )

    def _extract_url(self, line: str) -> Optional[str]:
        m = URL_PATTERN.search(line)
        return m.group(0).rstrip(".,;)\"'") if m else None

    def _extract_url_from_buffer(self) -> Optional[str]:
        for line in reversed(list(self._buffer)):
            url = self._extract_url(line)
            if url:
                return url
        return None

    def _extract_http_code(self, line: str) -> Optional[int]:
        m = HTTP_CODE_PATTERN.search(line)
        return int(m.group(1)) if m else None

    def _extract_exception(self, line: str) -> Optional[str]:
        exc_match = re.search(r'([\w.]+Exception[:\s][^\n]{0,120})', line)
        return exc_match.group(1).strip() if exc_match else None

    def _detect_pattern(self, intervals: List[float]) -> Optional[str]:
        if len(intervals) < 2:
            return None
        avg = sum(intervals) / len(intervals)
        std = (sum((i - avg) ** 2 for i in intervals) / len(intervals)) ** 0.5
        cv  = std / avg if avg else 0

        if cv < 0.2:
            return f"Regular (~{round(avg)}s entre erros — possível timeout/keep-alive)"
        if avg < 5:
            return "Rajada rápida (erros em sequência — possível retry storm)"
        if avg > 300:
            return f"Esporádico ({round(avg/60, 1)} min entre erros — possível problema intermitente de rede)"
        return f"Irregular (intervalo médio {round(avg)}s)"

    def _most_likely_cause(self, cats: Dict, pattern: Optional[str], avg_interval: Optional[float]) -> str:
        if not cats:
            return "Sem dados suficientes"

        top_cat = max(cats, key=cats.get)

        causes = {
            ErrorCategory.SSL_TLS.value:
                "Falha SSL/TLS — verifique se o servidor usa TLS 1.2+, e se o Network Security Config permite o certificado",
            ErrorCategory.CERTIFICATE.value:
                "Problema de certificado — pode ser certificate pinning desatualizado, CA não confiável, ou cert expirado",
            ErrorCategory.DNS.value:
                "Falha de DNS — host não encontrado; verifique se a URL base está correta no build e se o servidor está up",
            ErrorCategory.TIMEOUT.value:
                "Timeout — servidor lento ou keepalive configurado muito baixo; revise os timeouts no OkHttp/Retrofit",
            ErrorCategory.CONNECTION.value:
                "Conexão recusada/resetada — servidor pode estar recusando conexões ou o IP/porta está errado",
            ErrorCategory.HTTP.value:
                "Erro HTTP (4xx/5xx) — problema no servidor ou autenticação; analise o endpoint e o código de retorno",
            ErrorCategory.CLEARTEXT.value:
                "HTTP bloqueado — o app usa HTTP mas o Network Security Config não permite cleartext; forçar HTTPS ou ajustar config",
            ErrorCategory.SOCKET.value:
                "Erro de socket — conexão interrompida; possível problema de keepalive ou firewall reiniciando conexões",
        }

        base = causes.get(top_cat, "Causa desconhecida — analise o stack trace completo")

        if pattern and "Regular" in pattern and avg_interval and 25 < avg_interval < 120:
            base += f"\n⚠ Padrão regular (~{round(avg_interval)}s) sugere timeout de socket/keepalive configurado no servidor ou cliente."

        return base