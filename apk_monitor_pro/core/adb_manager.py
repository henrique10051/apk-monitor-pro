"""
ADB Manager - Gerenciamento avançado de ADB
Filtros por PID, detecção automática, configuração de proxy
Integrado com NetworkIncidentDetector para captura de erros de rede
"""

import subprocess
import re
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Callable

# Import robusto: funciona tanto como pacote quanto via load_module dinâmico
try:
    from .network_incident_detector import NetworkIncidentDetector, NetworkIncident
except ImportError:
    import importlib.util as _ilu
    _here = Path(__file__).parent
    _spec = _ilu.spec_from_file_location(
        "network_incident_detector",
        _here / "network_incident_detector.py"
    )
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    NetworkIncidentDetector = _mod.NetworkIncidentDetector
    NetworkIncident         = _mod.NetworkIncident


def get_adb_path():
    """
    Retorna caminho do ADB
    Procura primeiro no executável embutido, depois no PATH
    """
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
        adb_path = base_path / "adb" / "adb.exe" if sys.platform.startswith('win') else base_path / "adb" / "adb"
        if adb_path.exists():
            return str(adb_path)
    return "adb"


class ADBManager:
    """Gerencia todas as operações com ADB"""

    def __init__(self):
        self.device_id    = None
        self.package_pids = {}
        self.adb_path     = get_adb_path()

        # ── Detector de incidentes de rede ──────────────────────────────
        self.incident_detector = NetworkIncidentDetector(
            context_before=25,
            context_after=10,
        )
        # Callback opcional: chamado a cada novo incidente detectado
        # Assinatura: on_network_incident(incident: NetworkIncident) -> None
        self.on_network_incident: Optional[Callable[[NetworkIncident], None]] = None

    # ------------------------------------------------------------------
    # ADB básico
    # ------------------------------------------------------------------

    def check_adb_available(self) -> bool:
        """Verifica se ADB está disponível"""
        try:
            result = subprocess.run(
                [self.adb_path, "version"],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, Exception):
            return False

    def get_connected_devices(self) -> List[str]:
        """Lista dispositivos conectados"""
        try:
            result = subprocess.run(
                [self.adb_path, "devices"],
                capture_output=True, text=True
            )
            devices = []
            for line in result.stdout.split('\n')[1:]:
                if '\tdevice' in line:
                    devices.append(line.split('\t')[0])
            return devices
        except Exception:
            return []

    # ------------------------------------------------------------------
    # PID
    # ------------------------------------------------------------------

    def get_package_pid(self, package_name: str) -> Optional[int]:
        """
        Obtém PID de um pacote específico.

        Args:
            package_name: Nome do pacote (ex: it.overit.amplawfm)

        Returns:
            PID do processo ou None se não encontrado
        """
        try:
            result = subprocess.run(
                [self.adb_path, "shell", "pidof", package_name],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                pid = int(result.stdout.strip().split()[0])
                self.package_pids[package_name] = pid
                return pid

            # Fallback: ps + grep
            result = subprocess.run(
                [self.adb_path, "shell", "ps", "|", "grep", package_name],
                capture_output=True, text=True, shell=True, timeout=5
            )
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if package_name in line:
                        parts = line.split()
                        for part in parts:
                            if part.isdigit() and len(part) <= 6:
                                pid = int(part)
                                self.package_pids[package_name] = pid
                                return pid
            return None

        except Exception as e:
            print(f"Erro ao obter PID: {e}")
            return None

    def get_all_overit_pids(self) -> List[int]:
        """Obtém PIDs de TODOS os processos da Overit"""
        try:
            result = subprocess.run(
                [self.adb_path, "shell", "ps", "|", "grep", "overit"],
                capture_output=True, text=True, shell=True, timeout=5
            )
            pids = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if 'overit' in line.lower():
                        parts = line.split()
                        for part in parts:
                            if part.isdigit() and len(part) <= 6:
                                pids.append(int(part))
                                break
            return list(set(pids))
        except Exception as e:
            print(f"Erro ao obter PIDs Overit: {e}")
            return []

    # ------------------------------------------------------------------
    # Logcat — com detecção automática de incidentes de rede
    # ------------------------------------------------------------------

    def start_logcat_filtered(self, package_name: str, log_level: str = "V",
                              strict_mode: bool = True) -> subprocess.Popen:
        """
        Inicia logcat com filtro.

        Args:
            package_name: Nome do pacote
            log_level:    Nível de log (V, D, I, W, E, F)
            strict_mode:  True = apenas PID específico, False = qualquer Overit

        Returns:
            Processo do logcat
        """
        subprocess.run([self.adb_path, "logcat", "-c"], check=False)

        if strict_mode:
            pid = self.get_package_pid(package_name)
            if pid:
                cmd = [
                    self.adb_path, "logcat",
                    "-v", "threadtime",
                    "--pid", str(pid),
                    f"*:{log_level}"
                ]
            else:
                raise Exception(f"PID não encontrado para {package_name}. App está rodando?")
        else:
            cmd = [
                self.adb_path, "logcat",
                "-v", "threadtime",
                f"*:{log_level}"
            ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        return process

    def read_logcat_line(self, line: str):
        """
        Processa uma linha lida do logcat.

        Deve ser chamado no loop que lê o stdout do processo retornado por
        start_logcat_filtered(). Detecta automaticamente incidentes de rede
        e dispara o callback on_network_incident quando encontrar um.

        Exemplo de uso:
            process = manager.start_logcat_filtered(package)
            for raw_line in process.stdout:
                line = raw_line.strip()
                manager.read_logcat_line(line)   # <-- adicionar esta linha
                ui.append_log(line)              # sua lógica existente

        Args:
            line: Linha bruta do logcat (já com strip)
        """
        incident = self.incident_detector.feed(line)
        if incident and self.on_network_incident:
            self.on_network_incident(incident)

    def get_network_analysis(self) -> Dict:
        """
        Retorna análise consolidada dos incidentes de rede capturados.

        Returns:
            Dict com total, categorias, padrão e causa mais provável.
            Veja NetworkIncidentDetector.analyze() para o schema completo.
        """
        return self.incident_detector.analyze()

    def export_network_report(self, path: str = "network_incidents.json") -> str:
        """
        Exporta incidentes de rede para JSON.

        Args:
            path: Caminho do arquivo de saída

        Returns:
            Caminho do arquivo gerado
        """
        return self.incident_detector.export_report(path)

    def clear_network_incidents(self):
        """Limpa todos os incidentes de rede registrados."""
        self.incident_detector.clear()

    # ------------------------------------------------------------------
    # Proxy
    # ------------------------------------------------------------------

    def configure_proxy_reverse(self, port: int = 8888) -> bool:
        """
        Configura proxy usando ADB reverse (não requer root).

        Args:
            port: Porta do proxy

        Returns:
            True se configurado com sucesso
        """
        try:
            result = subprocess.run(
                [self.adb_path, "reverse", f"tcp:{port}", f"tcp:{port}"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Erro ao configurar proxy reverse: {e}")
            return False

    def configure_proxy_iptables(self, port: int = 8888, pc_ip: str = None) -> Dict:
        """
        Configura proxy usando iptables (REQUER ROOT).
        Redireciona TODO tráfego HTTP/HTTPS automaticamente.

        Args:
            port:  Porta do proxy
            pc_ip: IP do PC (detectado automaticamente se None)

        Returns:
            Dict com status e comandos executados
        """
        if not pc_ip:
            pc_ip = self.get_local_ip()

        results = {'success': True, 'commands': [], 'errors': []}

        try:
            check_root = subprocess.run(
                [self.adb_path, "shell", "su", "-c", "id"],
                capture_output=True, text=True, timeout=5
            )
            if check_root.returncode != 0:
                results['success'] = False
                results['errors'].append("Dispositivo não tem ROOT ou permissão negada")
                return results

            commands = [
                ("HTTP Redirect",  f"iptables -t nat -A OUTPUT -p tcp --dport 80 -j DNAT --to-destination {pc_ip}:{port}"),
                ("HTTPS Redirect", f"iptables -t nat -A OUTPUT -p tcp --dport 443 -j DNAT --to-destination {pc_ip}:{port}"),
            ]

            for name, cmd in commands:
                result = subprocess.run(
                    [self.adb_path, "shell", "su", "-c", cmd],
                    capture_output=True, text=True, timeout=5
                )
                results['commands'].append({
                    'name': name, 'command': cmd,
                    'success': result.returncode == 0,
                    'output': result.stdout + result.stderr
                })
                if result.returncode != 0:
                    results['success'] = False
                    results['errors'].append(f"{name} falhou: {result.stderr}")

            return results

        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Exceção: {str(e)}")
            return results

    def clear_iptables_rules(self) -> bool:
        """Limpa regras iptables (REQUER ROOT)"""
        try:
            result = subprocess.run(
                [self.adb_path, "shell", "su", "-c", "iptables -t nat -F"],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Utilitários de rede
    # ------------------------------------------------------------------

    def get_local_ip(self) -> str:
        """Obtém IP local do PC"""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def get_network_info(self) -> Dict:
        """Obtém informações de rede do dispositivo"""
        info = {
            'wifi_enabled': False,
            'connected': False,
            'ssid': None,
            'signal_strength': None,
            'ip_address': None
        }
        try:
            result = subprocess.run(
                [self.adb_path, "shell", "dumpsys", "wifi", "|", "grep", "Wi-Fi"],
                capture_output=True, text=True, shell=True, timeout=5
            )
            if 'enabled' in result.stdout.lower():
                info['wifi_enabled'] = True

            result = subprocess.run(
                [self.adb_path, "shell", "dumpsys", "wifi", "|", "grep", "mWifiInfo"],
                capture_output=True, text=True, shell=True, timeout=5
            )
            if result.stdout:
                m = re.search(r'SSID:\s*([^,]+)', result.stdout)
                if m:
                    info['ssid'] = m.group(1).strip()
                    info['connected'] = True
                m = re.search(r'rssi:\s*(-?\d+)', result.stdout)
                if m:
                    info['signal_strength'] = int(m.group(1))

            result = subprocess.run(
                [self.adb_path, "shell", "ip", "addr", "show", "wlan0"],
                capture_output=True, text=True, timeout=5
            )
            m = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            if m:
                info['ip_address'] = m.group(1)

        except Exception as e:
            print(f"Erro ao obter info de rede: {e}")

        return info

    def ping_server(self, host: str) -> Optional[float]:
        """
        Faz ping para servidor do dispositivo.

        Args:
            host: Hostname ou IP

        Returns:
            Latência média em ms ou None se falhou
        """
        try:
            result = subprocess.run(
                [self.adb_path, "shell", "ping", "-c", "3", host],
                capture_output=True, text=True, timeout=10
            )
            m = re.search(r'avg\s*=\s*([0-9.]+)', result.stdout)
            if m:
                return float(m.group(1))
            return None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Info do app
    # ------------------------------------------------------------------

    def get_app_info(self, package_name: str) -> Dict:
        """
        Obtém informações sobre a APK instalada.

        Args:
            package_name: Nome do pacote

        Returns:
            Dict com versão, path, data_dir, etc.
        """
        info = {
            'installed': False,
            'version': None,
            'version_code': None,
            'path': None,
            'data_dir': None
        }
        try:
            result = subprocess.run(
                [self.adb_path, "shell", "pm", "list", "packages", "|", "grep", package_name],
                capture_output=True, text=True, shell=True, timeout=5
            )
            if package_name not in result.stdout:
                return info

            info['installed'] = True

            result = subprocess.run(
                [self.adb_path, "shell", "dumpsys", "package", package_name],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout:
                for pattern, key in [
                    (r'versionName=([^\s]+)', 'version'),
                    (r'versionCode=(\d+)',    'version_code'),
                    (r'codePath=([^\s]+)',    'path'),
                    (r'dataDir=([^\s]+)',     'data_dir'),
                ]:
                    m = re.search(pattern, result.stdout)
                    if m:
                        info[key] = m.group(1)

        except Exception as e:
            print(f"Erro ao obter info do app: {e}")

        return info