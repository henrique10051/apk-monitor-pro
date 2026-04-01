"""
Error Diagnostics - Diagnóstico de Causa Raiz
Identifica camada do problema, responsável e ações
"""

from typing import Dict, List, Optional
from datetime import datetime
import re


class ErrorDiagnostics:
    """Diagnóstico avançado de erros"""
    
    # Categorias de erro por camada
    NETWORK_ERRORS = [
        'UnknownHostException',
        'SocketTimeoutException',
        'ConnectException',
        'SSLException',
        'SSLHandshakeException',
        'NoRouteToHostException',
        'BindException',
        'PortUnreachableException'
    ]
    
    APP_ERRORS = [
        'NullPointerException',
        'IllegalStateException',
        'IllegalArgumentException',
        'ClassCastException',
        'IndexOutOfBoundsException',
        'NumberFormatException',
        'ActivityNotFoundException'
    ]
    
    DATABASE_ERRORS = [
        'SQLiteException',
        'DatabaseLockedException',
        'SQLiteDiskIOException',
        'SQLiteFullException',
        'SQLiteCantOpenDatabaseException'
    ]
    
    SYNC_ERRORS = [
        'SyncException',
        'RemoteException',
        'OperationCanceledException'
    ]
    
    SERVER_ERRORS = [
        'HttpException',
        'ServerException',
        'JSONException',
        'ParseException'
    ]
    
    def __init__(self):
        self.error_history = []
        
    def diagnose_error(self, log_entry: Dict, network_context: Optional[List] = None,
                      timeline_events: Optional[List] = None) -> Dict:
        """
        Diagnóstico completo de um erro
        
        Args:
            log_entry: Log do erro
            network_context: Contexto de rede (requests/responses próximos)
            timeline_events: Eventos que antecederam o erro
            
        Returns:
            Dict com diagnóstico completo
        """
        message = log_entry.get('message', '')
        tag = log_entry.get('tag', '')
        
        diagnosis = {
            'timestamp': log_entry.get('timestamp'),
            'error_type': self._identify_error_type(message),
            'layer': self._identify_layer(message),
            'responsible_team': None,
            'root_cause': None,
            'evidence': [],
            'recommended_action': None,
            'severity': self._calculate_severity(log_entry),
            'timeline': timeline_events or [],
            'network_analysis': None,
            'technical_details': {}
        }
        
        # Diagnóstico específico por tipo
        if diagnosis['error_type'] in self.NETWORK_ERRORS:
            diagnosis.update(self._diagnose_network_error(log_entry, network_context))
        
        elif diagnosis['error_type'] in self.DATABASE_ERRORS:
            diagnosis.update(self._diagnose_database_error(log_entry))
        
        elif diagnosis['error_type'] in self.SYNC_ERRORS:
            diagnosis.update(self._diagnose_sync_error(log_entry, network_context, timeline_events))
        
        elif diagnosis['error_type'] in self.APP_ERRORS:
            diagnosis.update(self._diagnose_app_error(log_entry))
        
        elif diagnosis['error_type'] in self.SERVER_ERRORS:
            diagnosis.update(self._diagnose_server_error(log_entry, network_context))
        
        # Adiciona ao histórico
        self.error_history.append(diagnosis)
        
        return diagnosis
    
    def _identify_error_type(self, message: str) -> str:
        """Identifica tipo de exceção"""
        # Procura por Exception
        match = re.search(r'(\w+Exception|\w+Error)', message)
        if match:
            return match.group(1)
        
        # Procura por palavras-chave
        if 'timeout' in message.lower():
            return 'SocketTimeoutException'
        elif 'connection' in message.lower():
            return 'ConnectException'
        elif 'sync' in message.lower():
            return 'SyncException'
        
        return 'UnknownError'
    
    def _identify_layer(self, message: str) -> str:
        """Identifica camada onde erro ocorreu"""
        message_lower = message.lower()
        
        all_errors = {
            'NETWORK': self.NETWORK_ERRORS,
            'DATABASE': self.DATABASE_ERRORS,
            'APP': self.APP_ERRORS,
            'SYNC': self.SYNC_ERRORS,
            'SERVER': self.SERVER_ERRORS
        }
        
        for layer, errors in all_errors.items():
            for error in errors:
                if error.lower() in message_lower:
                    return layer
        
        return 'UNKNOWN'
    
    def _calculate_severity(self, log_entry: Dict) -> str:
        """Calcula severidade do erro"""
        level = log_entry.get('level', 'I')
        message = log_entry.get('message', '').lower()
        
        # Fatal = Crítico
        if level == 'F':
            return 'CRITICAL'
        
        # Palavras críticas
        critical_keywords = ['crash', 'fatal', 'outofmemory', 'anr']
        if any(k in message for k in critical_keywords):
            return 'CRITICAL'
        
        # Error = High
        if level == 'E':
            return 'HIGH'
        
        # Warning = Medium
        if level == 'W':
            return 'MEDIUM'
        
        return 'LOW'
    
    def _diagnose_network_error(self, log_entry: Dict, network_context: Optional[List]) -> Dict:
        """Diagnóstico de erro de rede"""
        message = log_entry['message']
        error_type = self._identify_error_type(message)
        
        diagnosis = {
            'layer': 'NETWORK',
            'responsible_team': 'INFRA/REDE',
            'evidence': []
        }
        
        # Análise específica por tipo
        if error_type == 'SocketTimeoutException':
            timeout_match = re.search(r'timeout.*?(\d+)', message, re.IGNORECASE)
            timeout_ms = int(timeout_match.group(1)) if timeout_match else 30000
            
            diagnosis['root_cause'] = f"Servidor não respondeu dentro do timeout ({timeout_ms}ms)"
            diagnosis['technical_details'] = {
                'timeout_configured': f"{timeout_ms}ms",
                'type': 'Read Timeout',
                'network_layer': 'TCP'
            }
            
            # Verifica contexto de rede
            if network_context:
                # Procura request correspondente
                matching_requests = [
                    req for req in network_context 
                    if req.get('type') == 'request' and 
                    abs((datetime.fromisoformat(req['timestamp']) - 
                         datetime.fromisoformat(log_entry['timestamp'])).total_seconds()) < 35
                ]
                
                if matching_requests:
                    last_request = matching_requests[-1]
                    diagnosis['evidence'].append(
                        f"Request enviado para {last_request.get('url', 'unknown')} "
                        f"mas servidor não respondeu"
                    )
                    diagnosis['technical_details']['endpoint'] = last_request.get('url')
                    diagnosis['technical_details']['method'] = last_request.get('method')
            
            diagnosis['evidence'].append("Conexão TCP estabelecida mas servidor não enviou dados a tempo")
            
            # Recomendação
            diagnosis['recommended_action'] = (
                "🎯 AÇÃO PARA INFRA/BACKEND:\n"
                "1. Investigar logs do servidor no momento do timeout\n"
                "2. Verificar queries lentas no banco de dados\n"
                "3. Analisar performance do endpoint específico\n"
                "4. Considerar aumentar timeout se processamento é realmente lento\n"
                "5. Otimizar endpoint para responder mais rápido"
            )
        
        elif error_type == 'UnknownHostException':
            host_match = re.search(r'Unable to resolve host[:\s]+"?([^":\s]+)', message)
            host = host_match.group(1) if host_match else 'unknown'
            
            diagnosis['root_cause'] = f"DNS não conseguiu resolver hostname: {host}"
            diagnosis['technical_details'] = {
                'hostname': host,
                'dns_lookup': 'FAILED',
                'possible_causes': [
                    'Sem conexão com internet',
                    'DNS não está resolvendo',
                    'Hostname incorreto',
                    'Firewall bloqueando DNS'
                ]
            }
            
            diagnosis['evidence'].append(f"Hostname '{host}' não foi resolvido pelo DNS")
            diagnosis['evidence'].append("Dispositivo pode estar sem internet ou DNS está falhando")
            
            diagnosis['recommended_action'] = (
                "🎯 AÇÃO PARA REDE:\n"
                "1. Verificar se dispositivo tem conexão com internet\n"
                "2. Testar resolução DNS: `nslookup {host}`\n"
                "3. Verificar configurações de DNS no dispositivo\n"
                "4. Confirmar se hostname está correto no código"
            ).format(host=host)
        
        elif error_type == 'ConnectException':
            diagnosis['root_cause'] = "Falha ao estabelecer conexão TCP com servidor"
            diagnosis['evidence'].append("Servidor recusou conexão ou está offline")
            diagnosis['evidence'].append("Porta pode estar bloqueada ou servidor não está escutando")
            
            diagnosis['recommended_action'] = (
                "🎯 AÇÃO PARA INFRA:\n"
                "1. Verificar se servidor está rodando\n"
                "2. Confirmar se porta está aberta e acessível\n"
                "3. Verificar firewall/security groups\n"
                "4. Testar conectividade com telnet/nc"
            )
        
        elif error_type == 'SSLException' or error_type == 'SSLHandshakeException':
            diagnosis['root_cause'] = "Falha na negociação SSL/TLS"
            diagnosis['technical_details'] = {
                'protocol': 'HTTPS',
                'possible_causes': [
                    'Certificado SSL expirado',
                    'Certificado não confiável',
                    'Data/hora do dispositivo incorreta',
                    'Versão SSL/TLS incompatível'
                ]
            }
            
            diagnosis['evidence'].append("Handshake SSL/TLS falhou")
            
            if 'certificate' in message.lower():
                diagnosis['evidence'].append("Problema relacionado a certificado SSL")
            
            if 'expired' in message.lower():
                diagnosis['evidence'].append("Certificado pode estar expirado")
                diagnosis['responsible_team'] = 'INFRA/SEGURANÇA'
            
            diagnosis['recommended_action'] = (
                "🎯 AÇÃO PARA INFRA/SEGURANÇA:\n"
                "1. Verificar validade do certificado SSL do servidor\n"
                "2. Confirmar data/hora do dispositivo está correta\n"
                "3. Verificar chain de certificados\n"
                "4. Testar com: `openssl s_client -connect host:443`"
            )
        
        return diagnosis
    
    def _diagnose_sync_error(self, log_entry: Dict, network_context: Optional[List],
                            timeline_events: Optional[List]) -> Dict:
        """Diagnóstico de erro de sincronização"""
        message = log_entry['message']
        
        diagnosis = {
            'layer': 'SYNC',
            'root_cause': 'Falha no processo de sincronização',
            'evidence': [],
            'technical_details': {}
        }
        
        # Analisa timeline para entender o que aconteceu
        if timeline_events:
            # Procura eventos relevantes
            db_queries = [e for e in timeline_events if 'sqlite' in str(e).lower() or 'database' in str(e).lower()]
            network_events = [e for e in timeline_events if 'http' in str(e).lower() or 'request' in str(e).lower()]
            
            if db_queries:
                diagnosis['evidence'].append(f"Encontradas {len(db_queries)} operações de banco de dados antes do erro")
                diagnosis['technical_details']['database_operations'] = len(db_queries)
            
            if network_events:
                diagnosis['evidence'].append(f"Encontradas {len(network_events)} operações de rede antes do erro")
                diagnosis['technical_details']['network_operations'] = len(network_events)
        
        # Analisa contexto de rede
        if network_context:
            # Procura última tentativa de sync
            sync_requests = [
                req for req in network_context
                if req.get('type') == 'request' and 
                ('sync' in req.get('url', '').lower() or 'sync' in req.get('path', '').lower())
            ]
            
            if sync_requests:
                last_sync = sync_requests[-1]
                
                # Procura response correspondente
                sync_responses = [
                    resp for resp in network_context
                    if resp.get('type') == 'response' and
                    resp.get('url') == last_sync.get('url')
                ]
                
                if sync_responses:
                    last_response = sync_responses[-1]
                    status_code = last_response.get('status_code', 0)
                    
                    diagnosis['technical_details']['last_sync_request'] = {
                        'url': last_sync.get('url'),
                        'method': last_sync.get('method'),
                        'timestamp': last_sync.get('timestamp')
                    }
                    
                    diagnosis['technical_details']['last_sync_response'] = {
                        'status_code': status_code,
                        'timestamp': last_response.get('timestamp')
                    }
                    
                    if status_code >= 500:
                        diagnosis['root_cause'] = f"Servidor retornou erro {status_code}"
                        diagnosis['responsible_team'] = 'BACKEND'
                        diagnosis['evidence'].append(f"Servidor retornou HTTP {status_code} (erro interno)")
                        
                    elif status_code >= 400:
                        diagnosis['root_cause'] = f"Request inválido - HTTP {status_code}"
                        diagnosis['responsible_team'] = 'DESENVOLVIMENTO'
                        diagnosis['evidence'].append(f"Servidor rejeitou request com HTTP {status_code}")
                        
                    elif status_code == 200:
                        diagnosis['root_cause'] = "Response OK mas processamento falhou"
                        diagnosis['responsible_team'] = 'DESENVOLVIMENTO'
                        diagnosis['evidence'].append("Servidor respondeu OK mas app não processou corretamente")
                
                else:
                    # Request enviado mas sem response
                    diagnosis['root_cause'] = "Request enviado mas servidor não respondeu"
                    diagnosis['responsible_team'] = 'INFRA/BACKEND'
                    diagnosis['evidence'].append("POST /sync enviado mas nenhuma resposta recebida")
                    diagnosis['evidence'].append("Possível timeout ou servidor travado")
        
        # Recomendações baseadas na causa
        if diagnosis.get('responsible_team') == 'BACKEND':
            diagnosis['recommended_action'] = (
                "🎯 AÇÃO PARA BACKEND:\n"
                "1. Investigar logs do servidor no momento do erro\n"
                "2. Verificar se dados recebidos estavam corretos\n"
                "3. Analisar regras de validação\n"
                "4. Verificar integridade do banco de dados"
            )
        elif diagnosis.get('responsible_team') == 'DESENVOLVIMENTO':
            diagnosis['recommended_action'] = (
                "🎯 AÇÃO PARA DESENVOLVIMENTO:\n"
                "1. Revisar lógica de sincronização\n"
                "2. Verificar tratamento de erros\n"
                "3. Validar payload antes de enviar\n"
                "4. Adicionar logs para debug"
            )
        else:
            diagnosis['recommended_action'] = (
                "🎯 AÇÃO MULTIDISCIPLINAR:\n"
                "1. DEV: Verificar código de sync\n"
                "2. BACKEND: Analisar logs do servidor\n"
                "3. INFRA: Verificar conectividade\n"
                "4. Reproduzir em ambiente controlado"
            )
        
        return diagnosis
    
    def _diagnose_database_error(self, log_entry: Dict) -> Dict:
        """Diagnóstico de erro de banco de dados"""
        message = log_entry['message']
        error_type = self._identify_error_type(message)
        
        diagnosis = {
            'layer': 'DATABASE',
            'responsible_team': 'DESENVOLVIMENTO',
            'evidence': [],
            'technical_details': {}
        }
        
        if error_type == 'DatabaseLockedException':
            diagnosis['root_cause'] = "Banco de dados bloqueado por outra operação"
            diagnosis['evidence'].append("Múltiplas threads tentando acessar DB simultaneamente")
            diagnosis['evidence'].append("Possível deadlock ou operação lenta travando DB")
            
            diagnosis['recommended_action'] = (
                "🎯 AÇÃO PARA DESENVOLVIMENTO:\n"
                "1. Revisar uso de transactions\n"
                "2. Implementar retry logic com backoff\n"
                "3. Verificar se há operações longas bloqueando\n"
                "4. Considerar usar WAL mode no SQLite"
            )
        
        elif error_type == 'SQLiteFullException':
            diagnosis['root_cause'] = "Espaço em disco insuficiente"
            diagnosis['evidence'].append("Dispositivo sem espaço para expandir banco de dados")
            diagnosis['responsible_team'] = 'DESENVOLVIMENTO/USUÁRIO'
            
            diagnosis['recommended_action'] = (
                "🎯 AÇÃO PARA DESENVOLVIMENTO:\n"
                "1. Implementar limpeza de dados antigos\n"
                "2. Adicionar verificação de espaço antes de gravar\n"
                "3. Alertar usuário quando espaço estiver baixo\n"
                "🎯 AÇÃO PARA USUÁRIO:\n"
                "1. Liberar espaço no dispositivo"
            )
        
        else:
            diagnosis['root_cause'] = f"Erro no banco de dados: {error_type}"
            diagnosis['recommended_action'] = (
                "🎯 AÇÃO PARA DESENVOLVIMENTO:\n"
                "1. Analisar query SQL que causou erro\n"
                "2. Verificar integridade do banco\n"
                "3. Considerar backup e restore"
            )
        
        return diagnosis
    
    def _diagnose_app_error(self, log_entry: Dict) -> Dict:
        """Diagnóstico de erro de aplicação"""
        message = log_entry['message']
        error_type = self._identify_error_type(message)
        
        diagnosis = {
            'layer': 'APP',
            'responsible_team': 'DESENVOLVIMENTO',
            'root_cause': f'Bug no código: {error_type}',
            'evidence': [],
            'technical_details': {}
        }
        
        # Extrai stack trace se disponível
        if 'at ' in message:
            stack_lines = [line.strip() for line in message.split('\n') if line.strip().startswith('at ')]
            if stack_lines:
                diagnosis['technical_details']['stack_trace'] = stack_lines[:5]  # Top 5
                diagnosis['evidence'].append(f"Stack trace disponível com {len(stack_lines)} frames")
        
        if error_type == 'NullPointerException':
            diagnosis['evidence'].append("Tentativa de acessar objeto nulo")
            diagnosis['recommended_action'] = (
                "🎯 AÇÃO PARA DESENVOLVIMENTO:\n"
                "1. Identificar variável nula no stack trace\n"
                "2. Adicionar null-check antes de usar\n"
                "3. Revisar fluxo de inicialização\n"
                "4. Usar Optional/nullable types adequadamente"
            )
        
        return diagnosis
    
    def _diagnose_server_error(self, log_entry: Dict, network_context: Optional[List]) -> Dict:
        """Diagnóstico de erro de servidor"""
        diagnosis = {
            'layer': 'SERVER',
            'responsible_team': 'BACKEND',
            'evidence': [],
            'technical_details': {}
        }
        
        # Procura response com erro
        if network_context:
            error_responses = [
                resp for resp in network_context
                if resp.get('type') == 'response' and
                resp.get('status_code', 0) >= 400
            ]
            
            if error_responses:
                last_error = error_responses[-1]
                status_code = last_error.get('status_code')
                
                diagnosis['root_cause'] = f"Servidor retornou HTTP {status_code}"
                diagnosis['technical_details']['status_code'] = status_code
                diagnosis['technical_details']['url'] = last_error.get('url')
                
                # Analisa response body
                content = last_error.get('content', '')
                if content:
                    diagnosis['technical_details']['server_response'] = content[:500]
                    diagnosis['evidence'].append(f"Servidor retornou mensagem: {content[:200]}")
        
        diagnosis['recommended_action'] = (
            "🎯 AÇÃO PARA BACKEND:\n"
            "1. Analisar logs do servidor\n"
            "2. Verificar regras de negócio\n"
            "3. Validar formato de dados\n"
            "4. Corrigir erro e deployar fix"
        )
        
        return diagnosis
    
    def generate_timeline(self, logs: List[Dict], error_log: Dict, 
                         window_seconds: int = 30) -> List[Dict]:
        """
        Gera timeline de eventos antes do erro
        
        Args:
            logs: Lista de todos os logs
            error_log: Log do erro
            window_seconds: Janela de tempo em segundos antes do erro
            
        Returns:
            Lista de eventos na timeline
        """
        # Parse do timestamp do erro (formato: MM-DD HH:MM:SS.mmm)
        error_ts_str = error_log['timestamp']
        
        try:
            # Tenta parse ISO format primeiro
            error_time = datetime.fromisoformat(error_ts_str)
        except ValueError:
            # Se falhar, tenta formato logcat: MM-DD HH:MM:SS.mmm
            try:
                from datetime import datetime as dt
                # Assume ano atual
                current_year = datetime.now().year
                # Adiciona ano ao timestamp
                error_ts_full = f"{current_year}-{error_ts_str}"
                error_time = datetime.strptime(error_ts_full, "%Y-%m-%d %H:%M:%S.%f")
            except:
                # Se ainda falhar, retorna vazio
                return []
        
        timeline = []
        
        for log in logs:
            try:
                log_ts_str = log['timestamp']
                
                # Tenta parse
                try:
                    log_time = datetime.fromisoformat(log_ts_str)
                except ValueError:
                    # Formato logcat
                    current_year = datetime.now().year
                    log_ts_full = f"{current_year}-{log_ts_str}"
                    log_time = datetime.strptime(log_ts_full, "%Y-%m-%d %H:%M:%S.%f")
                
                diff = (error_time - log_time).total_seconds()
                
                # Apenas eventos antes do erro dentro da janela
                if 0 <= diff <= window_seconds:
                    timeline.append({
                        'timestamp': log['timestamp'],
                        'seconds_before_error': round(diff, 3),
                        'level': log['level'],
                        'tag': log['tag'],
                        'message': log['message'][:200],
                        'event_type': self._classify_event(log)
                    })
            except Exception as e:
                # Ignora logs com timestamp inválido
                continue
        
        # Ordena por timestamp
        timeline.sort(key=lambda x: x['seconds_before_error'], reverse=True)
        
        return timeline
    
    def _classify_event(self, log: Dict) -> str:
        """Classifica tipo de evento"""
        message_lower = log['message'].lower()
        tag_lower = log['tag'].lower()
        
        if any(k in message_lower or k in tag_lower for k in ['sync', 'sincroniza']):
            return 'SYNC'
        elif any(k in message_lower or k in tag_lower for k in ['http', 'request', 'response']):
            return 'NETWORK'
        elif any(k in message_lower or k in tag_lower for k in ['sqlite', 'database', 'query']):
            return 'DATABASE'
        elif 'click' in message_lower or 'button' in message_lower:
            return 'USER_ACTION'
        elif log['level'] in ['E', 'F']:
            return 'ERROR'
        elif log['level'] == 'W':
            return 'WARNING'
        else:
            return 'INFO'