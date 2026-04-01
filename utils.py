"""
Utilitários auxiliares para APK Monitor Pro
Funções úteis para análise de logs e tráfego
"""

import json
import re
from datetime import datetime
from collections import Counter


class LogAnalyzer:
    """Analisador avançado de logs"""
    
    @staticmethod
    def find_crashes(logs):
        """Encontra todos os crashes nos logs"""
        crashes = []
        
        for i, log in enumerate(logs):
            if 'FATAL EXCEPTION' in log.get('message', ''):
                # Agrupa o crash com linhas seguintes
                crash_info = {
                    'timestamp': log['timestamp'],
                    'tag': log['tag'],
                    'message': log['message']
                }
                
                # Pega as próximas 10 linhas de stack trace
                stack_trace = []
                for j in range(i+1, min(i+11, len(logs))):
                    if logs[j].get('message', '').startswith('    at '):
                        stack_trace.append(logs[j]['message'])
                        
                crash_info['stack_trace'] = stack_trace
                crashes.append(crash_info)
                
        return crashes
    
    @staticmethod
    def find_exceptions(logs):
        """Encontra exceções nos logs"""
        exceptions = []
        exception_pattern = re.compile(r'(\w+Exception): (.+)')
        
        for log in logs:
            match = exception_pattern.search(log.get('message', ''))
            if match:
                exceptions.append({
                    'timestamp': log['timestamp'],
                    'exception_type': match.group(1),
                    'message': match.group(2),
                    'full_log': log['message']
                })
                
        return exceptions
    
    @staticmethod
    def find_patterns(logs, pattern):
        """Encontra padrão específico nos logs"""
        matches = []
        
        for log in logs:
            if re.search(pattern, log.get('message', ''), re.IGNORECASE):
                matches.append(log)
                
        return matches
    
    @staticmethod
    def get_most_common_errors(logs, top=10):
        """Retorna os erros mais comuns"""
        error_messages = [
            log['message'] for log in logs 
            if log.get('level') in ['E', 'F']
        ]
        
        # Agrupa mensagens similares (primeiras 50 caracteres)
        grouped = Counter([msg[:50] for msg in error_messages])
        
        return grouped.most_common(top)


class NetworkAnalyzer:
    """Analisador de tráfego de rede"""
    
    @staticmethod
    def find_failed_requests(traffic):
        """Encontra requests que falharam"""
        failed = []
        
        for item in traffic:
            if item.get('type') == 'response':
                status = item.get('status_code', 0)
                if status >= 400:
                    failed.append(item)
                    
        return failed
    
    @staticmethod
    def group_by_endpoint(traffic):
        """Agrupa requests por endpoint"""
        endpoints = {}
        
        for item in traffic:
            if item.get('type') == 'request':
                url = item.get('url', '')
                host = item.get('host', 'unknown')
                
                if host not in endpoints:
                    endpoints[host] = []
                    
                endpoints[host].append(item)
                
        return endpoints
    
    @staticmethod
    def find_slow_requests(traffic, threshold_ms=5000):
        """Encontra requests lentas (precisa calcular tempo de resposta)"""
        # Agrupa requests e responses
        pairs = []
        requests = {}
        
        for item in traffic:
            if item.get('type') == 'request':
                url = item.get('url')
                requests[url] = item
            elif item.get('type') == 'response':
                url = item.get('url')
                if url in requests:
                    req = requests[url]
                    pairs.append({
                        'request': req,
                        'response': item,
                        'url': url
                    })
                    
        return pairs
    
    @staticmethod
    def extract_api_calls(traffic):
        """Extrai todas as chamadas de API"""
        api_calls = []
        
        for item in traffic:
            if item.get('type') == 'request':
                api_calls.append({
                    'timestamp': item.get('timestamp'),
                    'method': item.get('method'),
                    'url': item.get('url'),
                    'headers': item.get('headers', {}),
                    'body': item.get('content', '')
                })
                
        return api_calls
    
    @staticmethod
    def find_data_leaks(traffic, sensitive_keywords):
        """Procura por vazamento de dados sensíveis"""
        leaks = []
        
        for item in traffic:
            content = item.get('content', '')
            
            for keyword in sensitive_keywords:
                if keyword.lower() in content.lower():
                    leaks.append({
                        'timestamp': item.get('timestamp'),
                        'type': item.get('type'),
                        'url': item.get('url'),
                        'keyword': keyword,
                        'context': content[:200]  # Primeiros 200 chars
                    })
                    
        return leaks


class ReportGenerator:
    """Gerador de relatórios personalizados"""
    
    @staticmethod
    def generate_crash_report(crashes):
        """Gera relatório de crashes"""
        report = []
        report.append("=" * 80)
        report.append("RELATÓRIO DE CRASHES")
        report.append("=" * 80)
        report.append("")
        
        if not crashes:
            report.append("✅ Nenhum crash detectado!")
            return "\n".join(report)
            
        report.append(f"⚠️  Total de crashes encontrados: {len(crashes)}")
        report.append("")
        
        for i, crash in enumerate(crashes, 1):
            report.append(f"[CRASH #{i}]")
            report.append(f"Timestamp: {crash['timestamp']}")
            report.append(f"Tag: {crash['tag']}")
            report.append(f"Mensagem: {crash['message']}")
            
            if crash.get('stack_trace'):
                report.append("Stack Trace:")
                for line in crash['stack_trace']:
                    report.append(f"  {line}")
                    
            report.append("")
            report.append("-" * 80)
            report.append("")
            
        return "\n".join(report)
    
    @staticmethod
    def generate_network_report(traffic_analysis):
        """Gera relatório de tráfego de rede"""
        report = []
        report.append("=" * 80)
        report.append("RELATÓRIO DE TRÁFEGO DE REDE")
        report.append("=" * 80)
        report.append("")
        
        if 'failed_requests' in traffic_analysis:
            failed = traffic_analysis['failed_requests']
            report.append(f"❌ Requests com erro: {len(failed)}")
            
            if failed:
                report.append("\nDetalhes dos erros:")
                for req in failed[:10]:  # Top 10
                    report.append(f"  - Status {req['status_code']}: {req['url']}")
                    
        report.append("")
        
        if 'endpoints' in traffic_analysis:
            endpoints = traffic_analysis['endpoints']
            report.append(f"📍 Total de endpoints acessados: {len(endpoints)}")
            report.append("\nTop endpoints:")
            
            sorted_endpoints = sorted(
                endpoints.items(), 
                key=lambda x: len(x[1]), 
                reverse=True
            )
            
            for host, requests in sorted_endpoints[:10]:
                report.append(f"  - {host}: {len(requests)} requests")
                
        return "\n".join(report)


def export_to_csv(data, filename, data_type='logs'):
    """Exporta dados para CSV"""
    import csv
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        if data_type == 'logs':
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'level', 'tag', 'message'])
            writer.writeheader()
            
            for log in data:
                writer.writerow({
                    'timestamp': log.get('timestamp', ''),
                    'level': log.get('level', ''),
                    'tag': log.get('tag', ''),
                    'message': log.get('message', '')
                })
                
        elif data_type == 'network':
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'type', 'url', 'status'])
            writer.writeheader()
            
            for item in data:
                writer.writerow({
                    'timestamp': item.get('timestamp', ''),
                    'type': item.get('type', ''),
                    'url': item.get('url', ''),
                    'status': item.get('status_code', '')
                })


def main():
    """Exemplo de uso dos utilitários"""
    print("=" * 60)
    print("APK Monitor Pro - Utilitários de Análise")
    print("=" * 60)
    print()
    print("Este módulo contém funções auxiliares para:")
    print("  - Análise avançada de logs")
    print("  - Análise de tráfego de rede")
    print("  - Geração de relatórios customizados")
    print()
    print("Importe este módulo no apk_monitor_pro.py:")
    print("  from utils import LogAnalyzer, NetworkAnalyzer")
    print()
    print("Exemplos de uso:")
    print("  crashes = LogAnalyzer.find_crashes(logs)")
    print("  failed = NetworkAnalyzer.find_failed_requests(traffic)")
    print()


if __name__ == "__main__":
    main()
