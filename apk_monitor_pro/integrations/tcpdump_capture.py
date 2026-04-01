"""
TCPDump Integration - Captura de pacotes de rede
Análise profunda de tráfego com Wireshark
"""

import subprocess
import time
import re
from typing import Optional, Dict, List
from pathlib import Path
from datetime import datetime


class TCPDumpCapture:
    """
    Captura de pacotes de rede usando tcpdump
    Permite análise posterior com Wireshark
    """
    
    def __init__(self):
        self.capture_process = None
        self.capture_file = None
        self.is_capturing = False
        
    def check_tcpdump_available(self) -> bool:
        """Verifica se tcpdump está disponível no dispositivo"""
        try:
            result = subprocess.run(
                ["adb", "shell", "which", "tcpdump"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return result.returncode == 0 and result.stdout.strip()
            
        except:
            return False
    
    def install_tcpdump(self) -> bool:
        """
        Tenta instalar tcpdump no dispositivo (requer root)
        
        Returns:
            True se instalou com sucesso
        """
        try:
            # Verifica root
            result = subprocess.run(
                ["adb", "shell", "su", "-c", "id"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print("❌ Dispositivo sem ROOT")
                return False
            
            # Download tcpdump
            # (usuário precisa ter baixado previamente)
            # https://www.androidtcpdump.com/
            
            print("⚠️  Baixe tcpdump de: https://www.androidtcpdump.com/")
            print("    Depois execute: adb push tcpdump /data/local/tmp/")
            
            return False
            
        except:
            return False
    
    def start_capture(self, output_file: Optional[str] = None, 
                     filter_expression: Optional[str] = None,
                     interface: str = "any") -> bool:
        """
        Inicia captura de pacotes
        
        Args:
            output_file: Arquivo .pcap de saída (gerado automaticamente se None)
            filter_expression: Filtro tcpdump (ex: "port 80 or port 443")
            interface: Interface de rede (padrão: any)
            
        Returns:
            True se iniciou com sucesso
        """
        if self.is_capturing:
            print("⚠️  Captura já está em andamento")
            return False
        
        try:
            # Arquivo de saída
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"/sdcard/capture_{timestamp}.pcap"
            
            self.capture_file = output_file
            
            # Comando tcpdump
            cmd = ["adb", "shell", "su", "-c"]
            
            tcpdump_cmd = f"tcpdump -i {interface} -s 0 -w {output_file}"
            
            if filter_expression:
                tcpdump_cmd += f" {filter_expression}"
            
            cmd.append(tcpdump_cmd)
            
            # Inicia processo
            self.capture_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Aguarda um pouco para garantir que iniciou
            time.sleep(1)
            
            if self.capture_process.poll() is None:
                self.is_capturing = True
                print(f"✅ Captura iniciada: {output_file}")
                if filter_expression:
                    print(f"   Filtro: {filter_expression}")
                return True
            else:
                stderr = self.capture_process.stderr.read()
                print(f"❌ Erro ao iniciar captura: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Exceção ao iniciar captura: {e}")
            return False
    
    def stop_capture(self) -> Optional[str]:
        """
        Para captura e retorna caminho do arquivo
        
        Returns:
            Caminho do arquivo .pcap ou None se falhou
        """
        if not self.is_capturing:
            print("⚠️  Nenhuma captura em andamento")
            return None
        
        try:
            # Mata processo tcpdump
            if self.capture_process:
                # Envia SIGINT para tcpdump
                subprocess.run(
                    ["adb", "shell", "su", "-c", "killall", "tcpdump"],
                    timeout=5
                )
                
                self.capture_process.wait(timeout=5)
            
            self.is_capturing = False
            
            # Verifica se arquivo foi criado
            result = subprocess.run(
                ["adb", "shell", "ls", "-lh", self.capture_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"✅ Captura finalizada: {self.capture_file}")
                return self.capture_file
            else:
                print("❌ Arquivo de captura não encontrado")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao parar captura: {e}")
            return None
    
    def pull_capture(self, local_path: Optional[str] = None) -> Optional[str]:
        """
        Baixa arquivo .pcap do dispositivo
        
        Args:
            local_path: Caminho local de destino (gerado automaticamente se None)
            
        Returns:
            Caminho do arquivo local ou None se falhou
        """
        if not self.capture_file:
            print("❌ Nenhum arquivo de captura disponível")
            return None
        
        try:
            # Caminho local
            if not local_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                local_path = f"./captures/capture_{timestamp}.pcap"
            
            # Cria diretório se não existir
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Pull do dispositivo
            result = subprocess.run(
                ["adb", "pull", self.capture_file, local_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"✅ Arquivo baixado: {local_path}")
                print(f"   Abra com Wireshark para análise detalhada")
                return local_path
            else:
                print(f"❌ Erro ao baixar arquivo: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao baixar captura: {e}")
            return None
    
    def analyze_capture(self, pcap_file: str) -> Dict:
        """
        Análise rápida do arquivo .pcap
        
        Args:
            pcap_file: Caminho do arquivo .pcap
            
        Returns:
            Dict com estatísticas básicas
        """
        analysis = {
            'total_packets': 0,
            'protocols': {},
            'hosts': set(),
            'ports': set(),
            'size_bytes': 0
        }
        
        try:
            # Usa tshark se disponível
            result = subprocess.run(
                ["tshark", "-r", pcap_file, "-q", "-z", "io,stat,0"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse output
                for line in result.stdout.split('\n'):
                    if 'frames' in line.lower():
                        match = re.search(r'(\d+)', line)
                        if match:
                            analysis['total_packets'] = int(match.group(1))
            
            # Protocolos
            result = subprocess.run(
                ["tshark", "-r", pcap_file, "-q", "-z", "io,phs"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                protocols = {}
                for line in result.stdout.split('\n'):
                    if '%' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            protocol = parts[0]
                            protocols[protocol] = protocols.get(protocol, 0) + 1
                
                analysis['protocols'] = protocols
            
            # Tamanho do arquivo
            import os
            analysis['size_bytes'] = os.path.getsize(pcap_file)
            
        except FileNotFoundError:
            print("⚠️  tshark não instalado. Instale Wireshark para análise detalhada.")
            
            # Fallback: apenas tamanho
            try:
                import os
                analysis['size_bytes'] = os.path.getsize(pcap_file)
            except:
                pass
        
        except Exception as e:
            print(f"❌ Erro na análise: {e}")
        
        return analysis
    
    def start_capture_for_app(self, package_name: str, duration: int = 60) -> Optional[str]:
        """
        Captura tráfego de uma APK específica
        
        Args:
            package_name: Nome do pacote
            duration: Duração em segundos
            
        Returns:
            Caminho do arquivo local .pcap ou None
        """
        # Pega UID da APK
        result = subprocess.run(
            ["adb", "shell", "dumpsys", "package", package_name, "|", "grep", "userId="],
            capture_output=True,
            text=True,
            shell=True,
            timeout=5
        )
        
        uid = None
        if result.returncode == 0:
            import re
            match = re.search(r'userId=(\d+)', result.stdout)
            if match:
                uid = match.group(1)
        
        # Filtro por UID (funciona em alguns Android)
        filter_expr = None
        if uid:
            filter_expr = f"user {uid}"
        
        # Inicia captura
        if self.start_capture(filter_expression=filter_expr):
            print(f"⏱️  Capturando por {duration} segundos...")
            print("   Use a APK normalmente agora!")
            
            time.sleep(duration)
            
            # Para captura
            pcap_remote = self.stop_capture()
            
            if pcap_remote:
                # Baixa arquivo
                return self.pull_capture()
        
        return None
    
    def get_filters_for_sync(self) -> List[str]:
        """
        Retorna filtros úteis para análise de sincronização
        
        Returns:
            Lista de filtros tcpdump
        """
        return [
            "port 80 or port 443",  # HTTP/HTTPS
            "tcp port 80 or tcp port 443",  # Apenas TCP
            "host api.overit.com",  # Host específico
            "dst port 443",  # Apenas saída HTTPS
            "tcp and (port 80 or port 443)",  # HTTP/HTTPS TCP
        ]


# Guia de Análise com Wireshark
WIRESHARK_ANALYSIS_GUIDE = """
═══════════════════════════════════════════════════════════════
            ANÁLISE DE CAPTURA COM WIRESHARK
═══════════════════════════════════════════════════════════════

Após capturar o tráfego, abra o arquivo .pcap no Wireshark para
análise detalhada.

📊 FILTROS ÚTEIS NO WIRESHARK:

1️⃣ Ver apenas HTTP/HTTPS:
   http or tls

2️⃣ Ver apenas comunicação com servidor específico:
   ip.dst == 192.168.1.100

3️⃣ Ver apenas POST requests:
   http.request.method == "POST"

4️⃣ Ver respostas com erro:
   http.response.code >= 400

5️⃣ Ver pacotes de sincronização:
   http.request.uri contains "sync"

6️⃣ Ver tráfego de uma APK específica:
   tcp.port == [porta da APK]

═══════════════════════════════════════════════════════════════

🔍 COMO INVESTIGAR ERRO DE SYNC:

1. Filtre por: http.request.uri contains "sync"

2. Encontre o POST /sync que falhou

3. Clique com botão direito → Follow → HTTP Stream

4. Você verá:
   - Request completo (headers + body)
   - Response do servidor
   - Tempo de resposta

5. Se timeout:
   - Verá request mas não response
   - Ou response incompleto

6. Se erro 500:
   - Verá response com código de erro
   - Mensagem de erro do servidor

═══════════════════════════════════════════════════════════════

💡 DICAS:

• Statistics → Conversations: Ver quem fala com quem
• Statistics → Protocol Hierarchy: Ver distribuição de protocolos
• Statistics → IO Graph: Ver tráfego ao longo do tempo
• Analyze → Expert Info: Ver problemas detectados automaticamente

═══════════════════════════════════════════════════════════════
"""
