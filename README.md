# Demo OCI Queue — Sistema de Pedidos

Aplicação didática com dois componentes independentes:

- **Produtor (Flask / porta 5000):** formulário que publica pedidos em JSON na OCI Queue.
- **Consumidor (Flask / porta 5001):** faz polling da fila, processa pedidos e exclui mensagens concluídas.
- **Falha simulada:** permite demonstrar visibility timeout e reentrega.
- **Dashboard:** métricas e histórico local em SQLite.

## Arquitetura

`Navegador -> Produtor -> OCI Queue -> Consumidor -> DeleteMessage`

O SQLite é usado apenas para o dashboard da demonstração. Os pedidos trafegam de verdade pela OCI Queue.

## 1. Pré-requisitos

- Python 3.10+
- Uma Queue criada na Oracle Cloud
- OCI API Key configurada no computador
- OCID da Queue
- **Messages Endpoint** da Queue
- Permissão para produzir e consumir mensagens

## 2. Configuração

Crie e ative um ambiente virtual.

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edite `.env`:

```env
OCI_QUEUE_ID=ocid1.queue.oc1....
OCI_QUEUE_MESSAGES_ENDPOINT=https://....messages.queue....oci.oraclecloud.com
OCI_CONFIG_FILE=~/.oci/config
OCI_PROFILE=DEFAULT
```

O arquivo padrão do SDK fica em `~/.oci/config`. Exemplo:

```ini
[DEFAULT]
user=ocid1.user.oc1....
fingerprint=aa:bb:cc:...
tenancy=ocid1.tenancy.oc1....
region=sa-saopaulo-1
key_file=C:\Users\SEU_USUARIO\.oci\oci_api_key.pem
```

Não envie sua chave privada nem o `.env` para o Git.

## 3. Política IAM

Para uma demonstração simples, o usuário/grupo precisa conseguir produzir e consumir. Uma política com `use queues` no compartment cobre operações como PutMessages/GetMessages/DeleteMessage. Em ambientes reais, aplique privilégio mínimo.

Exemplo conceitual (troque o grupo e compartment):

```text
Allow group NOME_DO_GRUPO to use queues in compartment NOME_DO_COMPARTMENT
```

## 4. Executar

Abra dois terminais na raiz do projeto.

Terminal 1:

```bash
python producer/app.py
```

Acesse `http://localhost:5000`.

Terminal 2:

```bash
python consumer/app.py
```

Acesse `http://localhost:5001`.

## 5. Roteiro de demonstração

1. Abra produtor e consumidor lado a lado.
2. Envie um pedido normal.
3. Mostre `ENVIADO -> RECEBIDO -> PROCESSADO`.
4. Explique que `PROCESSADO` só ocorre depois de `DeleteMessage`.
5. Envie outro pedido marcando **Simular falha no consumidor**.
6. Mostre os eventos `RECEBIDO -> ERRO`.
7. Como o consumidor não chama `DeleteMessage`, a mensagem poderá reaparecer depois do visibility timeout.
8. Mostre que a contagem de entregas cresce em novas tentativas.
9. Pause/retome o consumidor para demonstrar o desacoplamento: o produtor continua publicando mesmo sem processamento imediato.

## 6. Melhorias implementadas

- Payload JSON estruturado
- ID único por pedido
- Prioridade
- Falha proposital
- Long polling
- Visibility timeout
- Confirmação explícita via DeleteMessage
- Dashboard
- Métricas
- Histórico local
- Consumidor pausável
- Separação da integração OCI em service

## Observação importante

A OCI Queue usa um **Messages Endpoint** próprio para operações de mensagens. Copie esse endpoint dos detalhes da fila na Console OCI e coloque em `OCI_QUEUE_MESSAGES_ENDPOINT`.
