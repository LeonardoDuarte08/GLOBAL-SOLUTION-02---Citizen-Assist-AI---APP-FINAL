import json
import os
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from validador_url import carregar_chave


def analisar_url(url):
    url = url.strip()
    endereco = urlparse(url)
    if (not url or len(url) > 2048 or endereco.scheme not in ("http", "https")
            or not endereco.hostname or any(c.isspace() for c in url)):
        return {"status": "erro", "mensagem": "Informe uma URL completa começando com https://"}

    chave = os.getenv("GOOGLE_SAFE_BROWSING_KEY") or carregar_chave()
    if not chave:
        return {"status": "erro", "mensagem": "O verificador ainda não está configurado."}

    dados = {
        "client": {"clientId": "citizen-assist-ai", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}]
        }
    }
    requisicao = Request(
        "https://safebrowsing.googleapis.com/v4/threatMatches:find?key=" + chave,
        data=json.dumps(dados).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urlopen(requisicao, timeout=10) as resposta:
            conteudo = json.load(resposta)
        ameacas = conteudo.get("matches", [])
        if ameacas:
            tipos = sorted(set(a.get("threatType", "Ameaça identificada") for a in ameacas))
            return {"status": "perigo", "mensagem": "Encontramos uma possível ameaça neste link.",
                    "detalhes": ", ".join(tipos)}
        return {"status": "sem_ameacas", "mensagem": "Nenhuma ameaça conhecida foi encontrada.",
                "detalhes": "Isso não garante que o site seja seguro. Confira o endereço antes de acessar."}
    except HTTPError as erro:
        return {"status": "erro", "mensagem": "Não foi possível concluir a verificação.",
                "detalhes": f"Código da API: {erro.code}"}
    except (URLError, TimeoutError, ValueError):
        return {"status": "erro", "mensagem": "Não foi possível consultar o serviço agora.",
                "detalhes": "Tente novamente mais tarde."}
