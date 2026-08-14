"""
APK Monitor Pro v2.0 - Interface Gráfica Completa
Sistema Profissional de Diagnóstico de APKs Android

Integra TODOS os módulos em uma interface unificada
"""

import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
    from PyQt5.QtGui import QFont, QColor, QTextCursor
except ImportError:
    print("\n" + "="*70)
    print("PyQt5 não instalado!")
    print("="*70)
    print("\nVocê está em um venv. Instale manualmente:")
    print("\n  pip install PyQt5\n")
    print("Depois execute novamente:")
    print("  python apk_monitor_pro.py")
    print("="*70 + "\n")
    sys.exit(1)

# Adiciona path dos módulos
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Imports dos módulos - tenta de várias formas
try:
    from apk_monitor_pro.core.adb_manager import ADBManager
    from apk_monitor_pro.analyzers.error_diagnostics import ErrorDiagnostics
    from apk_monitor_pro.integrations.frida_hook import FridaHooker
    from apk_monitor_pro.integrations.tcpdump_capture import TCPDumpCapture
    from apk_monitor_pro.utils.report_generator import ReportGenerator
except ImportError:
    import importlib.util

    def load_module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    adb_mod  = load_module("adb_manager",      current_dir / "apk_monitor_pro" / "core" / "adb_manager.py")
    ADBManager = adb_mod.ADBManager

    diag_mod = load_module("error_diagnostics", current_dir / "apk_monitor_pro" / "analyzers" / "error_diagnostics.py")
    ErrorDiagnostics = diag_mod.ErrorDiagnostics

    frida_mod = load_module("frida_hook",        current_dir / "apk_monitor_pro" / "integrations" / "frida_hook.py")
    FridaHooker = frida_mod.FridaHooker

    tcp_mod  = load_module("tcpdump_capture",   current_dir / "apk_monitor_pro" / "integrations" / "tcpdump_capture.py")
    TCPDumpCapture = tcp_mod.TCPDumpCapture

    rep_mod  = load_module("report_generator",  current_dir / "apk_monitor_pro" / "utils" / "report_generator.py")
    ReportGenerator = rep_mod.ReportGenerator


# ---------------------------------------------------------------------------
# Thread de captura ADB
# ---------------------------------------------------------------------------

class ADBThread(QThread):
    log_signal      = pyqtSignal(dict)
    error_signal    = pyqtSignal(str)
    incident_signal = pyqtSignal(object)   # NetworkIncident

    def __init__(self, adb_mgr, pkg, level, strict):
        super().__init__()
        self.adb     = adb_mgr
        self.pkg     = pkg
        self.level   = level
        self.strict  = strict
        self.running = False
        self.proc    = None

    def run(self):
        self.running = True

        # Conecta callback do detector ao signal desta thread
        def _on_incident(incident):
            self.incident_signal.emit(incident)
        self.adb.on_network_incident = _on_incident

        try:
            self.proc = self.adb.start_logcat_filtered(self.pkg, self.level, self.strict)
            for line in self.proc.stdout:
                if not self.running:
                    break
                stripped = line.strip()

                # Alimenta detector de rede (emite incident_signal se detectar)
                self.adb.read_logcat_line(stripped)

                log = self._parse(stripped)
                if log:
                    self.log_signal.emit(log)
        except Exception as e:
            self.error_signal.emit(str(e))

    def _parse(self, line):
        try:
            p = line.split(None, 6)
            if len(p) < 7:
                return None
            return {
                'timestamp': f"{p[0]} {p[1]}",
                'pid':       p[2],
                'tid':       p[3],
                'level':     p[4],
                'tag':       p[5].rstrip(':'),
                'message':   p[6] if len(p) > 6 else '',
                'raw':       line,
            }
        except Exception:
            return None

    def stop(self):
        self.running = False
        if self.proc:
            self.proc.terminate()


# ---------------------------------------------------------------------------
# Widget de Incidentes de Rede (PyQt5)
# ---------------------------------------------------------------------------

class IncidentItemWidget(QWidget):
    """Card expandível para um incidente de rede."""

    CATEGORY_COLORS = {
        "SSL/TLS":                "#f44747",
        "Timeout":                "#ff8c00",
        "DNS":                    "#dcdcaa",
        "Conexão":                "#ce9178",
        "HTTP":                   "#4fc1ff",
        "Certificado":            "#c586c0",
        "Tráfego HTTP bloqueado": "#f44747",
        "Socket":                 "#ff8c00",
        "Desconhecido":           "#888888",
    }

    def __init__(self, incident, index, parent=None):
        super().__init__(parent)
        self.incident = incident
        self.expanded = False
        self._build(index)

    def _build(self, index):
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 1)
        self._outer.setSpacing(0)

        # Header
        self._header = QWidget()
        self._header.setStyleSheet("background:#2d2d30; border-bottom:1px solid #3c3c3c;")
        self._header.setCursor(Qt.PointingHandCursor)
        hl = QHBoxLayout(self._header)
        hl.setContentsMargins(10, 6, 10, 6)

        cat   = self.incident.category.value
        color = self.CATEGORY_COLORS.get(cat, "#888")
        ts    = self.incident.timestamp.strftime("%H:%M:%S.%f")[:-3]

        num = QLabel(f"#{index+1:02d}")
        num.setStyleSheet("color:#666; font-family:Consolas; font-size:11px;")
        hl.addWidget(num)

        badge = QLabel(f" {cat} ")
        badge.setStyleSheet(f"background:{color}; color:#1e1e1e; font-weight:bold; "
                            f"font-size:10px; padding:2px 6px; border-radius:3px;")
        hl.addWidget(badge)

        ts_lbl = QLabel(ts)
        ts_lbl.setStyleSheet("color:#666; font-family:Consolas; font-size:11px; margin-left:8px;")
        hl.addWidget(ts_lbl)

        if self.incident.endpoint:
            ep = self.incident.endpoint
            if len(ep) > 55:
                ep = ep[:52] + "..."
            ep_lbl = QLabel(ep)
            ep_lbl.setStyleSheet("color:#9cdcfe; font-family:Consolas; font-size:11px; margin-left:8px;")
            hl.addWidget(ep_lbl)

        if self.incident.http_code:
            code_color = "#f44747" if self.incident.http_code >= 500 else "#ff8c00"
            code_lbl = QLabel(str(self.incident.http_code))
            code_lbl.setStyleSheet(f"color:{code_color}; font-weight:bold; font-size:11px; margin-left:8px;")
            hl.addWidget(code_lbl)

        if self.incident.interval_from_last is not None:
            int_lbl = QLabel(f"+{self.incident.interval_from_last:.1f}s")
            int_lbl.setStyleSheet("color:#555; font-size:10px; margin-left:6px;")
            hl.addWidget(int_lbl)

        hl.addStretch()

        self._arrow = QLabel("▶")
        self._arrow.setStyleSheet("color:#555; font-size:10px;")
        hl.addWidget(self._arrow)

        self._header.mousePressEvent = lambda e: self._toggle()
        self._outer.addWidget(self._header)

        # Corpo (oculto por default)
        self._body = QWidget()
        self._body.setStyleSheet("background:#252526;")
        bl = QVBoxLayout(self._body)
        bl.setContentsMargins(12, 8, 12, 8)
        bl.setSpacing(4)

        self._add_section(bl, "Linha que disparou:", [self.incident.trigger_line], "#f44747")
        if self.incident.raw_exception:
            self._add_section(bl, "Exception:", [self.incident.raw_exception], "#ff8c00")
        if self.incident.context_before:
            self._add_section(bl, f"Contexto ({len(self.incident.context_before)} linhas antes):",
                              self.incident.context_before, "#666")
        if self.incident.context_after:
            self._add_section(bl, f"Contexto ({len(self.incident.context_after)} linhas após):",
                              self.incident.context_after, "#666")

        self._body.hide()
        self._outer.addWidget(self._body)

    def _add_section(self, layout, label, lines, color):
        lbl = QLabel(label)
        lbl.setStyleSheet("color:#555; font-size:10px; font-weight:bold; margin-top:4px;")
        layout.addWidget(lbl)

        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setFont(QFont("Consolas", 9))
        txt.setStyleSheet(f"background:#1e1e1e; color:{color}; border:none; padding:4px;")
        txt.setPlainText("\n".join(lines))
        txt.setMaximumHeight(min(len(lines), 8) * 16 + 12)
        layout.addWidget(txt)

    def _toggle(self):
        self.expanded = not self.expanded
        self._body.setVisible(self.expanded)
        self._arrow.setText("▼" if self.expanded else "▶")


class NetworkIncidentsWidget(QWidget):
    """
    Aba completa de Incidentes de Rede para o QTabWidget existente.
    Recebe incidentes via add_incident() chamado do ADBThread.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._incident_count = 0
        self._build_ui()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar ───────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setStyleSheet("background:#252526; border-bottom:1px solid #3c3c3c;")
        toolbar.setFixedHeight(44)
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(12, 0, 8, 0)

        self._count_lbl = QLabel("0 incidentes")
        self._count_lbl.setStyleSheet("color:#666; font-size:12px;")
        tl.addWidget(self._count_lbl)

        self._last_lbl = QLabel("")
        self._last_lbl.setStyleSheet("color:#555; font-size:11px; margin-left:12px;")
        tl.addWidget(self._last_lbl)

        tl.addStretch()

        for label, slot, color in [
            ("🔍 Analisar",      self._show_analysis, "#0e7fd4"),
            ("↓ Exportar JSON",  self._export,        "#37373d"),
            ("⟳ Limpar",         self._clear,         "#37373d"),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet(f"background:{color}; color:white; border:none; "
                              f"padding:6px 12px; border-radius:4px; font-size:11px;")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(slot)
            tl.addWidget(btn)

        root.addWidget(toolbar)

        # ── Corpo: lista + painel análise ─────────────────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("background:#1e1e1e;")

        # Lista de incidentes
        left = QWidget()
        left.setStyleSheet("background:#1e1e1e;")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:#1e1e1e;")

        self._list_container = QWidget()
        self._list_container.setStyleSheet("background:#1e1e1e;")
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(4, 4, 4, 4)
        self._list_layout.setSpacing(2)
        self._list_layout.setAlignment(Qt.AlignTop)

        self._empty_lbl = QLabel("Nenhum incidente de rede detectado ainda.\n"
                                  "Os erros aparecerão aqui automaticamente.")
        self._empty_lbl.setStyleSheet("color:#444; font-size:13px;")
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._list_layout.addWidget(self._empty_lbl)

        scroll.setWidget(self._list_container)
        ll.addWidget(scroll)
        self._scroll = scroll

        splitter.addWidget(left)

        # Painel de análise
        right = QWidget()
        right.setStyleSheet("background:#252526;")
        right.setMinimumWidth(280)
        right.setMaximumWidth(340)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(12, 12, 12, 12)
        rl.setSpacing(8)

        self._build_analysis_panel(rl)
        splitter.addWidget(right)
        splitter.setSizes([900, 300])

        root.addWidget(splitter)

    def _build_analysis_panel(self, layout):
        title = QLabel("Análise")
        title.setStyleSheet("color:white; font-size:14px; font-weight:bold;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#3c3c3c;")
        layout.addWidget(sep)

        # Métricas
        self._metrics = {}
        for key, label in [("total", "Total"), ("interval", "Intervalo médio"), ("pattern", "Padrão")]:
            row = QWidget()
            row.setStyleSheet("background:transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 2, 0, 2)
            lbl = QLabel(label + ":")
            lbl.setStyleSheet("color:#555; font-size:11px;")
            lbl.setFixedWidth(110)
            val = QLabel("—")
            val.setStyleSheet("color:#ccc; font-size:11px; font-weight:bold;")
            val.setWordWrap(True)
            rl.addWidget(lbl)
            rl.addWidget(val, 1)
            layout.addWidget(row)
            self._metrics[key] = val

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color:#3c3c3c;")
        layout.addWidget(sep2)

        cat_title = QLabel("Categorias")
        cat_title.setStyleSheet("color:#aaa; font-size:12px; font-weight:bold; margin-top:4px;")
        layout.addWidget(cat_title)

        self._cat_widget = QWidget()
        self._cat_widget.setStyleSheet("background:transparent;")
        self._cat_layout = QVBoxLayout(self._cat_widget)
        self._cat_layout.setContentsMargins(0, 0, 0, 0)
        self._cat_layout.setSpacing(3)
        layout.addWidget(self._cat_widget)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setStyleSheet("color:#3c3c3c;")
        layout.addWidget(sep3)

        cause_title = QLabel("Causa mais provável")
        cause_title.setStyleSheet("color:#aaa; font-size:12px; font-weight:bold; margin-top:4px;")
        layout.addWidget(cause_title)

        self._cause_txt = QTextEdit()
        self._cause_txt.setReadOnly(True)
        self._cause_txt.setFont(QFont("Segoe UI", 9))
        self._cause_txt.setStyleSheet("background:#1e1e1e; color:#ff8c00; border:none; padding:6px;")
        self._cause_txt.setMaximumHeight(120)
        layout.addWidget(self._cause_txt)

        ep_title = QLabel("Endpoints afetados")
        ep_title.setStyleSheet("color:#aaa; font-size:12px; font-weight:bold; margin-top:4px;")
        layout.addWidget(ep_title)

        self._ep_txt = QTextEdit()
        self._ep_txt.setReadOnly(True)
        self._ep_txt.setFont(QFont("Consolas", 9))
        self._ep_txt.setStyleSheet("background:#1e1e1e; color:#9cdcfe; border:none; padding:6px;")
        self._ep_txt.setMaximumHeight(100)
        layout.addWidget(self._ep_txt)

        layout.addStretch()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def add_incident(self, incident):
        """Chamado pelo ADBThread via signal quando um incidente é detectado."""
        if self._empty_lbl.isVisible():
            self._empty_lbl.hide()

        card = IncidentItemWidget(incident, self._incident_count)
        self._list_layout.addWidget(card)
        self._incident_count += 1

        # Atualiza toolbar
        n = self._incident_count
        self._count_lbl.setText(f"{n} incidente{'s' if n != 1 else ''}")
        self._count_lbl.setStyleSheet("color:#f44747; font-size:12px; font-weight:bold;")
        self._last_lbl.setText(
            f"último: {incident.timestamp.strftime('%H:%M:%S')} — {incident.category.value}"
        )

        # Auto-scroll
        QTimer.singleShot(50, lambda: self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        ))

        self._refresh_analysis(incident)

    def _refresh_analysis(self, last_incident):
        # Coleta todos os incidentes dos cards
        cats = {}
        endpoints = set()
        intervals = []
        for i in range(self._list_layout.count()):
            w = self._list_layout.itemAt(i).widget()
            if not isinstance(w, IncidentItemWidget):
                continue
            c = w.incident.category.value
            cats[c] = cats.get(c, 0) + 1
            if w.incident.endpoint:
                endpoints.add(w.incident.endpoint)
            if w.incident.interval_from_last is not None:
                intervals.append(w.incident.interval_from_last)

        self._metrics["total"].setText(str(self._incident_count))

        if intervals:
            avg = sum(intervals) / len(intervals)
            self._metrics["interval"].setText(f"{avg:.1f}s")

            if len(intervals) >= 2:
                std = (sum((x - avg)**2 for x in intervals) / len(intervals)) ** 0.5
                cv  = std / avg if avg else 0
                if cv < 0.2:
                    pattern = f"Regular (~{round(avg)}s)"
                elif avg < 5:
                    pattern = "Rajada rápida"
                elif avg > 300:
                    pattern = f"Esporádico ({avg/60:.1f}min)"
                else:
                    pattern = f"Irregular (média {round(avg)}s)"
                self._metrics["pattern"].setText(pattern)

        # Categorias
        for i in reversed(range(self._cat_layout.count())):
            self._cat_layout.itemAt(i).widget().deleteLater()

        COLORS = {
            "SSL/TLS": "#f44747", "Timeout": "#ff8c00", "DNS": "#dcdcaa",
            "Conexão": "#ce9178", "HTTP": "#4fc1ff", "Certificado": "#c586c0",
            "Tráfego HTTP bloqueado": "#f44747", "Socket": "#ff8c00", "Desconhecido": "#888",
        }
        for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
            row = QWidget()
            row.setStyleSheet("background:transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            color = COLORS.get(cat, "#888")
            lbl = QLabel(f"● {cat}")
            lbl.setStyleSheet(f"color:{color}; font-size:11px;")
            cnt_lbl = QLabel(str(cnt))
            cnt_lbl.setStyleSheet(f"color:{color}; font-size:11px; font-weight:bold;")
            rl.addWidget(lbl)
            rl.addStretch()
            rl.addWidget(cnt_lbl)
            self._cat_layout.addWidget(row)

        # Causa raiz
        top_cat = max(cats, key=cats.get) if cats else None
        causes = {
            "SSL/TLS":                "Falha SSL/TLS — verifique TLS 1.2+ no servidor e o Network Security Config",
            "Certificado":            "Problema de certificado — certificate pinning desatualizado, CA não confiável ou cert expirado",
            "DNS":                    "Falha de DNS — host não encontrado; verifique a URL base no build",
            "Timeout":                "Timeout — servidor lento ou keepalive muito baixo; revise timeouts no OkHttp/Retrofit",
            "Conexão":                "Conexão recusada/resetada — servidor recusando conexões ou IP/porta errado",
            "HTTP":                   "Erro HTTP (4xx/5xx) — problema no servidor ou autenticação",
            "Tráfego HTTP bloqueado": "HTTP bloqueado pelo Network Security Config — force HTTPS ou ajuste a config",
            "Socket":                 "Erro de socket — possível problema de keepalive ou firewall reiniciando conexões",
        }
        cause = causes.get(top_cat, "Analise o stack trace completo") if top_cat else "—"

        # Dica extra para padrão regular
        if intervals and len(intervals) >= 2:
            avg = sum(intervals) / len(intervals)
            if 25 < avg < 120:
                cause += f"\n\n⚠ Padrão regular (~{round(avg)}s) sugere timeout de socket/keepalive."

        self._cause_txt.setPlainText(cause)
        self._ep_txt.setPlainText("\n".join(endpoints) if endpoints else "—")

    def _show_analysis(self):
        if self._incident_count == 0:
            QMessageBox.information(self, "Análise", "Nenhum incidente detectado ainda.")
            return

        # Coleta dados para exibir
        cats = {}
        for i in range(self._list_layout.count()):
            w = self._list_layout.itemAt(i).widget()
            if isinstance(w, IncidentItemWidget):
                c = w.incident.category.value
                cats[c] = cats.get(c, 0) + 1

        lines = [
            f"Total de incidentes: {self._incident_count}",
            "",
            "Distribuição por categoria:",
        ]
        for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
            lines.append(f"  {cat}: {cnt}")

        QMessageBox.information(self, "Análise de Incidentes", "\n".join(lines))

    def _export(self):
        incidents = []
        for i in range(self._list_layout.count()):
            w = self._list_layout.itemAt(i).widget()
            if isinstance(w, IncidentItemWidget):
                inc = w.incident
                incidents.append({
                    "timestamp":    inc.timestamp.isoformat(),
                    "category":     inc.category.value,
                    "trigger":      inc.trigger_line,
                    "endpoint":     inc.endpoint,
                    "http_code":    inc.http_code,
                    "interval_s":   inc.interval_from_last,
                    "exception":    inc.raw_exception,
                    "context_before": inc.context_before,
                    "context_after":  inc.context_after,
                })

        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Incidentes",
            f"network_incidents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON (*.json)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"total": self._incident_count, "incidents": incidents},
                          f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Exportado", f"✅ Salvo em:\n{path}")

    def _clear(self):
        if QMessageBox.question(self, "Limpar", "Limpar todos os incidentes?") != QMessageBox.Yes:
            return
        for i in reversed(range(self._list_layout.count())):
            w = self._list_layout.itemAt(i).widget()
            if isinstance(w, IncidentItemWidget):
                w.deleteLater()
        self._incident_count = 0
        self._empty_lbl.show()
        self._count_lbl.setText("0 incidentes")
        self._count_lbl.setStyleSheet("color:#666; font-size:12px;")
        self._last_lbl.setText("")
        self._cause_txt.clear()
        self._ep_txt.clear()
        for key in self._metrics:
            self._metrics[key].setText("—")


# ---------------------------------------------------------------------------
# Interface principal
# ---------------------------------------------------------------------------

class APKMonitorUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.adb    = ADBManager()
        self.diag   = ErrorDiagnostics()
        self.report = ReportGenerator()
        self.tcpdump = TCPDumpCapture()

        self.logs       = []
        self.errors     = []
        self.monitoring = False
        self.thread     = None

        self.pkgs = {
            0: "it.overit.amplawfm",
            1: "it.overit.enelsaopaulowfm",
            2: "it.overit.coelcewfm",
            3: "custom"
        }

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("APK Monitor Pro v2.0 - Diagnóstico Profissional")
        self.setGeometry(50, 50, 1700, 950)

        w = QWidget()
        self.setCentralWidget(w)
        layout = QVBoxLayout(w)

        layout.addWidget(self.make_header())

        self.tabs = QTabWidget()
        self.tabs.addTab(self.make_logs(),     "📱 Logs")
        self.tabs.addTab(self.make_diag(),     "🔍 Diagnóstico")
        self.tabs.addTab(self.make_timeline(), "⏱️ Timeline")
        self.tabs.addTab(self.make_frida(),    "🔗 Frida")
        self.tabs.addTab(self.make_reports(),  "📄 Relatórios")

        # Aba de incidentes de rede
        self.incidents_widget = NetworkIncidentsWidget()
        self.tabs.addTab(self.incidents_widget, "🔴 Incidentes")

        layout.addWidget(self.tabs)
        self.statusBar().showMessage("Pronto")

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def make_header(self):
        g = QGroupBox("Configurações")
        l = QHBoxLayout()

        l.addWidget(QLabel("APK:"))
        self.pkg_combo = QComboBox()
        self.pkg_combo.addItems(["🇧🇷 Rio", "🇧🇷 SP", "🇧🇷 CE", "📦 Outro"])
        self.pkg_combo.currentIndexChanged.connect(self.pkg_changed)
        l.addWidget(self.pkg_combo)

        self.pkg_input = QLineEdit()
        self.pkg_input.setPlaceholderText("Pacote personalizado")
        self.pkg_input.hide()
        l.addWidget(self.pkg_input)

        l.addWidget(QLabel("Filtro:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["🎯 Rígido (PID)", "🔄 Flexível"])
        l.addWidget(self.filter_combo)

        l.addWidget(QLabel("Nível:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["V", "D", "I", "W", "E"])
        self.level_combo.setCurrentIndex(2)
        l.addWidget(self.level_combo)

        l.addStretch()

        proxy_btn = QPushButton("🌐 Config Proxy")
        proxy_btn.clicked.connect(self.config_proxy)
        proxy_btn.setStyleSheet("background:#FF9800;color:white;padding:10px;font-weight:bold")
        l.addWidget(proxy_btn)

        self.start_btn = QPushButton("▶️ INICIAR")
        self.start_btn.clicked.connect(self.start)
        self.start_btn.setStyleSheet("background:#4CAF50;color:white;padding:12px;font-weight:bold")
        l.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹️ PARAR")
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("background:#f44336;color:white;padding:12px;font-weight:bold")
        l.addWidget(self.stop_btn)

        g.setLayout(l)
        return g

    # ------------------------------------------------------------------
    # Abas
    # ------------------------------------------------------------------

    def make_logs(self):
        w = QWidget()
        l = QVBoxLayout()

        info = QHBoxLayout()
        self.dev_lbl = QLabel("📱 Verificando...")
        info.addWidget(self.dev_lbl)
        self.pid_lbl = QLabel("🔢 PID: -")
        info.addWidget(self.pid_lbl)
        l.addLayout(info)

        f = QHBoxLayout()
        self.f_err     = QCheckBox("Erros");    self.f_err.toggled.connect(self.reapply_filters);    f.addWidget(self.f_err)
        self.f_sync    = QCheckBox("Sync");     self.f_sync.toggled.connect(self.reapply_filters);   f.addWidget(self.f_sync)
        self.f_network = QCheckBox("Network");  self.f_network.toggled.connect(self.reapply_filters);f.addWidget(self.f_network)
        self.f_sqlite  = QCheckBox("SQLite");   self.f_sqlite.toggled.connect(self.reapply_filters); f.addWidget(self.f_sqlite)
        self.f_http    = QCheckBox("HTTP");     self.f_http.toggled.connect(self.reapply_filters);   f.addWidget(self.f_http)
        f.addStretch()
        clear = QPushButton("🗑️")
        clear.clicked.connect(self.clear)
        f.addWidget(clear)
        l.addLayout(f)

        self.log_txt = QTextEdit()
        self.log_txt.setReadOnly(True)
        self.log_txt.setFont(QFont("Consolas", 9))
        l.addWidget(self.log_txt)

        self.stats = QLabel("📊 0 logs")
        l.addWidget(self.stats)

        w.setLayout(l)
        return w

    def make_diag(self):
        w = QWidget()
        l = QVBoxLayout()
        l.addWidget(QLabel("<h2>🔍 Diagnóstico de Causa Raiz</h2>"))
        self.diag_list = QListWidget()
        self.diag_list.itemClicked.connect(self.show_diag)
        l.addWidget(self.diag_list)
        self.diag_txt = QTextEdit()
        self.diag_txt.setReadOnly(True)
        l.addWidget(self.diag_txt)
        w.setLayout(l)
        return w

    def make_timeline(self):
        w = QWidget()
        l = QVBoxLayout()
        l.addWidget(QLabel("<h2>⏱️ Timeline de Eventos</h2>"))
        tl = QHBoxLayout()
        tl.addWidget(QLabel("Erro:"))
        self.tl_combo = QComboBox()
        tl.addWidget(self.tl_combo)
        btn = QPushButton("Gerar")
        btn.clicked.connect(self.gen_timeline)
        tl.addWidget(btn)
        l.addLayout(tl)
        self.tl_txt = QTextEdit()
        self.tl_txt.setReadOnly(True)
        self.tl_txt.setFont(QFont("Consolas", 9))
        l.addWidget(self.tl_txt)
        w.setLayout(l)
        return w

    def make_frida(self):
        w = QWidget()
        l = QVBoxLayout()
        l.addWidget(QLabel("<h2>🔗 Frida Hooking</h2>"))

        hooker = FridaHooker("test")
        if hooker.check_frida_available():
            lbl = QLabel("✅ Frida disponível")
            lbl.setStyleSheet("background:#C8E6C9;padding:10px")
            self.frida_available = True
        else:
            lbl = QLabel("⚠️ Frida não instalado. Instale com: pip install frida frida-tools")
            lbl.setStyleSheet("background:#FFECB3;padding:10px")
            self.frida_available = False
        l.addWidget(lbl)

        if self.frida_available:
            setup_group = QGroupBox("⚙️ Setup Frida Server")
            setup_layout = QVBoxLayout()
            info = QLabel("Frida Server precisa estar rodando no dispositivo Android.\n"
                          "Clique abaixo para verificar/iniciar automaticamente.")
            info.setWordWrap(True)
            setup_layout.addWidget(info)
            check_btn = QPushButton("🔍 Verificar Frida Server")
            check_btn.clicked.connect(self.check_frida_server_status)
            check_btn.setStyleSheet("background:#2196F3;color:white;padding:8px")
            setup_layout.addWidget(check_btn)
            setup_group.setLayout(setup_layout)
            l.addWidget(setup_group)

            hooks_group = QGroupBox("🎯 Hooks Disponíveis")
            hooks_layout = QVBoxLayout()
            for label, hook, color in [
                ("🔄 Hook Métodos de Sincronização", "sync",   "#2196F3"),
                ("💾 Hook Queries SQLite",           "sqlite", "#4CAF50"),
                ("🌐 Hook Requests HTTP",            "http",   "#FF9800"),
            ]:
                btn = QPushButton(label)
                btn.clicked.connect(lambda _, h=hook: self.start_frida_hook(h))
                btn.setStyleSheet(f"background:{color};color:white;padding:10px")
                hooks_layout.addWidget(btn)
            hooks_group.setLayout(hooks_layout)
            l.addWidget(hooks_group)

        self.frida_txt = QTextEdit()
        self.frida_txt.setReadOnly(True)
        self.frida_txt.setFont(QFont("Consolas", 9))
        self.frida_txt.setPlaceholderText("Hooks capturados aparecerão aqui...")
        l.addWidget(self.frida_txt)
        w.setLayout(l)
        return w

    def make_reports(self):
        w = QWidget()
        l = QVBoxLayout()
        l.addWidget(QLabel("<h2>📄 Exportar Dados do Monitoramento</h2>"))
        info = QLabel("O relatório consolida todos os logs capturados, eventos de rede e "
                      "diagnósticos de erro em um único arquivo.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; margin-bottom: 20px;")
        l.addWidget(info)
        for label, tipo, color in [
            ("{ } Exportar JSON (Dados Brutos)",     "json", "#2196F3"),
            ("🌐 Exportar HTML (Dashboard Visual)",  "html", "#4CAF50"),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, t=tipo: self.gen_report(t))
            btn.setStyleSheet(f"background:{color};color:white;padding:15px;font-weight:bold;font-size:14px;")
            l.addWidget(btn)
        l.addStretch()
        w.setLayout(l)
        return w

    # ------------------------------------------------------------------
    # Lógica
    # ------------------------------------------------------------------

    def pkg_changed(self, i):
        self.pkg_input.setVisible(i == 3)

    def get_pkg(self):
        i = self.pkg_combo.currentIndex()
        return self.pkg_input.text() if i == 3 else self.pkgs[i]

    def check_dev(self):
        if self.adb.check_adb_available():
            devs = self.adb.get_connected_devices()
            if devs:
                self.dev_lbl.setText(f"📱 {devs[0]} ✅")
            else:
                self.dev_lbl.setText("📱 Nenhum ⚠️")
        else:
            self.dev_lbl.setText("📱 ADB não encontrado ❌")
            if sys.platform.startswith('win'):
                QMessageBox.critical(self, "ADB não encontrado",
                    "ADB não foi encontrado!\n\n"
                    "1. Baixe: https://developer.android.com/tools/releases/platform-tools\n"
                    "2. Extraia para C:\\platform-tools\n"
                    "3. Adicione ao PATH\n"
                    "4. Reinicie o APK Monitor Pro\n\n"
                    "Teste no CMD: adb version")

    def config_proxy(self):
        r = QMessageBox.question(self, "Proxy",
            "ADB Reverse (simples)?\n\nYes = ADB Reverse\nNo = iptables (root)")
        if r == QMessageBox.Yes:
            if self.adb.configure_proxy_reverse(8888):
                QMessageBox.information(self, "OK", "✅ Proxy configurado via ADB Reverse!")
            else:
                QMessageBox.warning(self, "Erro", "❌ Falha")
        else:
            res = self.adb.configure_proxy_iptables(8888)
            if res['success']:
                QMessageBox.information(self, "OK", "✅ Proxy via iptables!")
            else:
                QMessageBox.critical(self, "Erro", "\n".join(res['errors']))

    def start(self):
        self.check_dev()
        if not self.adb.check_adb_available():
            QMessageBox.critical(self, "ADB não encontrado",
                "ADB não está instalado ou não está no PATH!\n\n"
                "macOS: brew install android-platform-tools\n"
                "Windows: https://developer.android.com/tools/releases/platform-tools")
            return

        pkg = self.get_pkg()
        if not pkg:
            QMessageBox.warning(self, "Atenção", "Selecione a APK!")
            return

        devs = self.adb.get_connected_devices()
        if not devs:
            QMessageBox.warning(self, "Nenhum dispositivo",
                "Nenhum dispositivo Android conectado!\n\n"
                "1. Conecte via USB\n"
                "2. Habilite 'Depuração USB'\n"
                "3. Aceite a mensagem no dispositivo\n"
                "4. Execute: adb devices")
            return

        strict = (self.filter_combo.currentIndex() == 0)
        if strict:
            pid = self.adb.get_package_pid(pkg)
            if pid:
                self.pid_lbl.setText(f"🔢 PID: {pid}")
            else:
                QMessageBox.warning(self, "Erro", "PID não encontrado!\nAPK está rodando?")
                return

        level = self.level_combo.currentText()

        # Reseta incidentes da sessão anterior
        self.adb.clear_network_incidents()

        try:
            self.thread = ADBThread(self.adb, pkg, level, strict)
            self.thread.log_signal.connect(self.on_log)
            self.thread.error_signal.connect(lambda e: QMessageBox.critical(self, "Erro", e))

            # Conecta o signal de incidente direto ao widget de incidentes
            self.thread.incident_signal.connect(self.incidents_widget.add_incident)

            self.thread.start()
            self.monitoring = True
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.statusBar().showMessage(f"✅ Monitorando {pkg}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao iniciar", str(e))

    def stop(self):
        if self.thread:
            self.thread.stop()
            self.thread.wait()
        self.monitoring = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.statusBar().showMessage("⏹️ Parado")

    def on_log(self, log):
        self.logs.append(log)

        if log['level'] in ['E', 'F', 'W']:
            d = self.diag.diagnose_error(log)
            if d.get('layer') != 'UNKNOWN':
                self.errors.append({'log': log, 'diag': d})
                self.diag_list.addItem(f"[{log['timestamp']}] {d.get('error_type', 'Erro')}")
                self.tl_combo.addItem(f"[{log['timestamp']}] {d.get('error_type', 'Erro')}")

        if self._passes_filters(log):
            colors = {'V':'#888','D':'#00F','I':'#080','W':'#F80','E':'#F00','F':'#800'}
            c = colors.get(log['level'], '#000')
            self.log_txt.append(
                f"<span style='color:{c}'>[{log['timestamp']}] "
                f"{log['level']}/{log['tag']}: {log['message']}</span>"
            )

        self.stats.setText(f"📊 {len(self.logs)} logs | {len(self.errors)} erros")

    def _passes_filters(self, log) -> bool:
        any_active = any([
            self.f_err.isChecked(), self.f_sync.isChecked(),
            self.f_network.isChecked(), self.f_sqlite.isChecked(), self.f_http.isChecked()
        ])
        if not any_active:
            return True

        msg = log['message'].lower()
        tag = log['tag'].lower()

        if self.f_err.isChecked()     and log['level'] in ['E', 'F', 'W']:               return True
        if self.f_sync.isChecked()    and ('sync' in msg or 'sync' in tag):               return True
        if self.f_network.isChecked() and any(k in msg or k in tag for k in
                                               ['network','connect','socket','http','ssl']): return True
        if self.f_sqlite.isChecked()  and any(k in msg or k in tag for k in
                                               ['sqlite','database','sql']):               return True
        if self.f_http.isChecked()    and any(k in msg or k in tag for k in
                                               ['http','request','response','okhttp']):    return True
        return False

    def clear(self):
        self.logs.clear()
        self.errors.clear()
        self.log_txt.clear()
        self.diag_list.clear()
        self.tl_combo.clear()
        self.stats.setText("📊 0 logs")

    def reapply_filters(self):
        self.log_txt.clear()
        colors = {'V':'#888','D':'#00F','I':'#080','W':'#F80','E':'#F00','F':'#800'}
        for log in self.logs:
            if self._passes_filters(log):
                c = colors.get(log['level'], '#000')
                self.log_txt.append(
                    f"<span style='color:{c}'>[{log['timestamp']}] "
                    f"{log['level']}/{log['tag']}: {log['message']}</span>"
                )

    def show_diag(self, item):
        i = self.diag_list.currentRow()
        if i < 0 or i >= len(self.errors):
            return
        d = self.errors[i]['diag']
        self.diag_txt.setHtml(f"""
<h1>🔍 Diagnóstico</h1>
<div style='background:#E3F2FD;padding:15px;margin:10px'>
<h3>Camada</h3><p><b>{d.get('layer','UNKNOWN')}</b></p></div>
<div style='background:#FFF3CD;padding:15px;margin:10px'>
<h3>Responsável</h3><p><b>{d.get('responsible_team','N/A')}</b></p></div>
<div style='background:#F5F5F5;padding:15px;margin:10px'>
<h3>Causa Raiz</h3><p>{d.get('root_cause','N/A')}</p></div>
<div style='background:#E8F5E9;padding:15px;margin:10px'>
<h3>Ação</h3><pre>{d.get('recommended_action','N/A')}</pre></div>
""")

    def gen_timeline(self):
        i = self.tl_combo.currentIndex()
        if i < 0 or i >= len(self.errors):
            return
        err_log = self.errors[i]['log']
        tl = self.diag.generate_timeline(self.logs, err_log, 30)
        out = ["="*80, "TIMELINE: 30s antes do erro", "="*80, ""]
        for e in tl:
            out.append(f"-{e['seconds_before_error']:05.2f}s | {e['tag']}: {e['message'][:60]}")
        self.tl_txt.setPlainText("\n".join(out))

    def gen_report(self, tipo):
        try:
            ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
            pkg_name = str(self.get_pkg())
            payload  = {
                "timestamp": ts,
                "apk":       str(self.pkg_combo.currentText()),
                "package":   pkg_name,
                "logs":      list(self.logs),
                "network":   [],
                "errors":    list(self.errors),
            }
            if tipo == 'json':
                content     = self.report.generate_json(payload)
                fn          = f"relatorio_apk_{ts}.json"
                file_filter = "JSON (*.json)"
            else:
                content     = self.report.generate_html(payload)
                fn          = f"relatorio_apk_{ts}.html"
                file_filter = "HTML (*.html)"

            path, _ = QFileDialog.getSaveFileName(
                self, "Salvar Relatório", fn, file_filter,
                options=QFileDialog.Options() | QFileDialog.DontUseNativeDialog
            )
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                QMessageBox.information(self, "OK", f"✅ Relatório salvo em:\n{path}")
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            QMessageBox.critical(self, "Erro na Geração", str(e))

    def start_frida_hook(self, hook_type):
        if not self.frida_available:
            QMessageBox.warning(self, "Frida não disponível",
                                "Instale: pip install frida frida-tools")
            return
        pkg = self.get_pkg()
        if not pkg:
            QMessageBox.warning(self, "Atenção", "Selecione a APK primeiro!")
            return
        hooker = FridaHooker(pkg)
        if not hooker.check_frida_server():
            reply = QMessageBox.question(self, "Frida Server",
                "Frida Server não está rodando.\nDeseja iniciar automaticamente? (Requer ROOT)",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.frida_txt.append("<b>🔄 Iniciando frida-server...</b><br>")
                if not hooker.start_frida_server():
                    QMessageBox.critical(self, "Erro",
                        "Não foi possível iniciar frida-server!\n\n"
                        "adb push frida-server /data/local/tmp/\n"
                        "adb shell 'su -c chmod 755 /data/local/tmp/frida-server'\n"
                        "adb shell 'su -c /data/local/tmp/frida-server &'")
                    return
            else:
                return
        self.frida_txt.append(f"<b style='color:green'>✅ Hook '{hook_type}' iniciado</b><br>")

    def check_frida_server_status(self):
        hooker = FridaHooker("test")
        self.frida_txt.append("<b>🔍 Verificando Frida Server...</b><br>")
        if hooker.check_frida_server():
            self.frida_txt.append("<b style='color:green'>✅ Frida Server está rodando!</b><br>")
            QMessageBox.information(self, "Status", "✅ Frida Server está rodando!")
        else:
            self.frida_txt.append("<b style='color:orange'>⚠️ Frida Server NÃO está rodando</b><br>")
            reply = QMessageBox.question(self, "Frida Server",
                "Deseja tentar iniciar automaticamente? (Requer ROOT)",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                if hooker.start_frida_server():
                    self.frida_txt.append("<b style='color:green'>✅ Iniciado!</b><br>")
                else:
                    self.frida_txt.append("<b style='color:red'>❌ Falha</b><br>")
                    QMessageBox.critical(self, "Erro", "Não foi possível iniciar frida-server.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui  = APKMonitorUI()
    ui.show()
    sys.exit(app.exec_())