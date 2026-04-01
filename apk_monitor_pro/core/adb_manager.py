"""
ADB Manager - Gerenciamento avançado de ADB
Filtros por PID, detecção automática, configuração de proxy
"""

import subprocess
import re
from typing import Optional, List, Dict


class ADBManager:
    """Gerencia todas as operações com ADB"""
    
    def __init__(self):
        self.device_id = None
        self.package_pids = {}
        
    def check_adb_available(self) -> bool:
        """Verifica se ADB está disponível"""
        try:
            result = subprocess.run(
                ["adb", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def get_connected_devices(self) -> List[str]:
        """Lista dispositivos conectados"""
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True
            )
            
            devices = []
            for line in result.stdout.split('\n')[1:]:
                if '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    devices.append(device_id)
            
            return devices
        except:
            return []
    
    def get_package_pid(self, package_name: str) -> Optional[int]:
        """
        Obtém PID de um pacote específico
        
        Args:
            package_name: Nome do pacote (ex: it.overit.amplawfm)
            
        Returns:
            PID do processo ou None se não encontrado
        """
        try:
            # Tenta ps (Android novo)
            result = subprocess.run(
                ["adb", "shell", "pidof", package_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                pid = int(result.stdout.strip().split()[0])
                self.package_pids[package_name] = pid
                return pid
            
            # Fallback: ps + grep
            result = subprocess.run(
                ["adb", "shell", "ps", "|", "grep", package_name],
                capture_output=True,
                text=True,
                shell=True,
                timeout=5
            )
            
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if package_name in line:
                        parts = line.split()
                        # PID geralmente é a segunda coluna
                        for i, part in enumerate(parts):
                            if part.isdigit() and len(part) <= 6:
                                pid = int(part)
                                self.package_pids[package_name] = pid
                                return pid
            
            return None
            
        except Exception as e:
            print(f"Erro ao obter PID: {e}")
            return None
    
    def get_all_overit_pids(self) -> List[int]:
        """
        Obtém PIDs de TODOS os processos da Overit
        
        Returns:
            Lista de PIDs
        """
        try:
            result = subprocess.run(
                ["adb", "shell", "ps", "|", "grep", "overit"],
                capture_output=True,
                text=True,
                shell=True,
                timeout=5
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
            
            return list(set(pids))  # Remove duplicatas
            
        except Exception as e:
            print(f"Erro ao obter PIDs Overit: {e}")
            return []
    
    def start_logcat_filtered(self, package_name: str, log_level: str = "V", 
                             strict_mode: bool = True) -> subprocess.Popen:
        """
        Inicia logcat com filtro
        
        Args:
            package_name: Nome do pacote
            log_level: Nível de log (V, D, I, W, E, F)
            strict_mode: True = apenas PID específico, False = qualquer Overit
            
        Returns:
            Processo do logcat
        """
        # Limpa buffer
        subprocess.run(["adb", "logcat", "-c"], check=False)
        
        if strict_mode:
            # Modo Rígido: Apenas PID específico
            pid = self.get_package_pid(package_name)
            
            if pid:
                cmd = [
                    "adb", "logcat",
                    "-v", "threadtime",
                    "--pid", str(pid),
                    f"*:{log_level}"
                ]
            else:
                raise Exception(f"PID não encontrado para {package_name}. App está rodando?")
        else:
            # Modo Flexível: Qualquer processo Overit
            cmd = [
                "adb", "logcat",
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
    
    def configure_proxy_reverse(self, port: int = 8888) -> bool:
        """
        Configura proxy usando ADB reverse (não requer root)
        
        Args:
            port: Porta do proxy
            
        Returns:
            True se configurado com sucesso
        """
        try:
            # ADB reverse
            result = subprocess.run(
                ["adb", "reverse", f"tcp:{port}", f"tcp:{port}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Erro ao configurar proxy reverse: {e}")
            return False
    
    def configure_proxy_iptables(self, port: int = 8888, pc_ip: str = None) -> Dict:
        """
        Configura proxy usando iptables (REQUER ROOT)
        Redireciona TODO tráfego HTTP/HTTPS automaticamente
        
        Args:
            port: Porta do proxy
            pc_ip: IP do PC (detectado automaticamente se None)
            
        Returns:
            Dict com status e comandos executados
        """
        if not pc_ip:
            pc_ip = self.get_local_ip()
        
        commands = []
        results = {
            'success': True,
            'commands': [],
            'errors': []
        }
        
        try:
            # 1. Verifica root
            check_root = subprocess.run(
                ["adb", "shell", "su", "-c", "id"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if check_root.returncode != 0:
                results['success'] = False
                results['errors'].append("Dispositivo não tem ROOT ou permissão negada")
                return results
            
            # 2. Redireciona HTTP (porta 80) para proxy
            cmd_http = f"iptables -t nat -A OUTPUT -p tcp --dport 80 -j DNAT --to-destination {pc_ip}:{port}"
            commands.append(("HTTP Redirect", cmd_http))
            
            # 3. Redireciona HTTPS (porta 443) para proxy
            cmd_https = f"iptables -t nat -A OUTPUT -p tcp --dport 443 -j DNAT --to-destination {pc_ip}:{port}"
            commands.append(("HTTPS Redirect", cmd_https))
            
            # 4. Executa comandos
            for name, cmd in commands:
                result = subprocess.run(
                    ["adb", "shell", "su", "-c", cmd],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                results['commands'].append({
                    'name': name,
                    'command': cmd,
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
        """
        Limpa regras iptables (REQUER ROOT)
        
        Returns:
            True se limpou com sucesso
        """
        try:
            result = subprocess.run(
                ["adb", "shell", "su", "-c", "iptables -t nat -F"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return result.returncode == 0
            
        except:
            return False
    
    def get_local_ip(self) -> str:
        """
        Obtém IP local do PC
        
        Returns:
            IP address
        """
        try:
            import socket
            
            # Cria socket temporário
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            
            return ip
        except:
            return "127.0.0.1"
    
    def get_network_info(self) -> Dict:
        """
        Obtém informações de rede do dispositivo
        
        Returns:
            Dict com info de WiFi, sinal, etc
        """
        info = {
            'wifi_enabled': False,
            'connected': False,
            'ssid': None,
            'signal_strength': None,
            'ip_address': None
        }
        
        try:
            # WiFi status
            result = subprocess.run(
                ["adb", "shell", "dumpsys", "wifi", "|", "grep", "Wi-Fi"],
                capture_output=True,
                text=True,
                shell=True,
                timeout=5
            )
            
            if 'enabled' in result.stdout.lower():
                info['wifi_enabled'] = True
            
            # SSID
            result = subprocess.run(
                ["adb", "shell", "dumpsys", "wifi", "|", "grep", "mWifiInfo"],
                capture_output=True,
                text=True,
                shell=True,
                timeout=5
            )
            
            if result.stdout:
                # Parse SSID
                match = re.search(r'SSID:\s*([^,]+)', result.stdout)
                if match:
                    info['ssid'] = match.group(1).strip()
                    info['connected'] = True
                
                # Parse signal strength
                match = re.search(r'rssi:\s*(-?\d+)', result.stdout)
                if match:
                    info['signal_strength'] = int(match.group(1))
            
            # IP Address
            result = subprocess.run(
                ["adb", "shell", "ip", "addr", "show", "wlan0"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                info['ip_address'] = match.group(1)
            
        except Exception as e:
            print(f"Erro ao obter info de rede: {e}")
        
        return info
    
    def ping_server(self, host: str) -> Optional[float]:
        """
        Faz ping para servidor do dispositivo
        
        Args:
            host: Hostname ou IP
            
        Returns:
            Latência em ms ou None se falhou
        """
        try:
            result = subprocess.run(
                ["adb", "shell", "ping", "-c", "3", host],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Parse tempo médio
            match = re.search(r'avg\s*=\s*([0-9.]+)', result.stdout)
            if match:
                return float(match.group(1))
            
            return None
            
        except:
            return None
    
    def get_app_info(self, package_name: str) -> Dict:
        """
        Obtém informações sobre a APK
        
        Args:
            package_name: Nome do pacote
            
        Returns:
            Dict com versão, path, etc
        """
        info = {
            'installed': False,
            'version': None,
            'version_code': None,
            'path': None,
            'data_dir': None
        }
        
        try:
            # Verifica se está instalado
            result = subprocess.run(
                ["adb", "shell", "pm", "list", "packages", "|", "grep", package_name],
                capture_output=True,
                text=True,
                shell=True,
                timeout=5
            )
            
            if package_name in result.stdout:
                info['installed'] = True
            else:
                return info
            
            # Pega info do pacote
            result = subprocess.run(
                ["adb", "shell", "dumpsys", "package", package_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.stdout:
                # Version
                match = re.search(r'versionName=([^\s]+)', result.stdout)
                if match:
                    info['version'] = match.group(1)
                
                # Version Code
                match = re.search(r'versionCode=(\d+)', result.stdout)
                if match:
                    info['version_code'] = match.group(1)
                
                # Path
                match = re.search(r'codePath=([^\s]+)', result.stdout)
                if match:
                    info['path'] = match.group(1)
                
                # Data dir
                match = re.search(r'dataDir=([^\s]+)', result.stdout)
                if match:
                    info['data_dir'] = match.group(1)
            
        except Exception as e:
            print(f"Erro ao obter info do app: {e}")
        
        return info
