# Pré-processamento de texto (`--preprocessar` / `-p`)

Expande abreviações, moeda, porcentagem, ordinais, siglas e números para PT-BR antes de enviar ao engine TTS. Evita que o modelo leia "R$" como "cifrão" ou "3º" como "três grau".

## Ativar o pré-processamento

```bash
.venv/bin/python tts_ptbr.py --preprocessar "R$ 1.250,50"
# lê: "mil duzentos e cinquenta reais e cinquenta centavos"

.venv/bin/python tts_ptbr.py -p "Dr. Silva ficou em 3º lugar com 98,5%"
# lê: "Doutor Silva ficou em terceiro lugar com noventa e oito vírgula cinco por cento"
```

## Moeda

```bash
.venv/bin/python tts_ptbr.py -p "Preço: R$ 10,00"
# → "Preço: dez reais"

.venv/bin/python tts_ptbr.py -p "Custa R$ 1.299,99"
# → "Custa mil duzentos e noventa e nove reais e noventa e nove centavos"

.venv/bin/python tts_ptbr.py -p "R$ 0,50 de troco"
# → "cinquenta centavos de troco"

.venv/bin/python tts_ptbr.py -p "R$ 1,00 por litro"
# → "um real por litro"
```

## Porcentagem

```bash
.venv/bin/python tts_ptbr.py -p "Taxa de 5%"
# → "Taxa de cinco por cento"

.venv/bin/python tts_ptbr.py -p "Crescimento de 12,7%"
# → "Crescimento de doze vírgula sete por cento"

.venv/bin/python tts_ptbr.py -p "100% aprovados"
# → "cem por cento aprovados"
```

## Ordinais

```bash
.venv/bin/python tts_ptbr.py -p "Chegou em 1º lugar"
# → "Chegou em primeiro lugar"

.venv/bin/python tts_ptbr.py -p "Está na 2ª posição"
# → "Está na segunda posição"

.venv/bin/python tts_ptbr.py -p "Completou o 10º ano"
# → "Completou o décimo ano"
```

## Abreviações

```bash
.venv/bin/python tts_ptbr.py -p "Dr. Carlos e Dra. Ana"
# → "Doutor Carlos e Doutora Ana"

.venv/bin/python tts_ptbr.py -p "Sr. João e Sra. Maria"
# → "Senhor João e Senhora Maria"

.venv/bin/python tts_ptbr.py -p "Prof. Rocha e Profa. Lima"
# → "Professor Rocha e Professora Lima"

.venv/bin/python tts_ptbr.py -p "Eng. Pereira, Av. Paulista, nº 100"
# → "Engenheiro Pereira, Avenida Paulista, número cem"

.venv/bin/python tts_ptbr.py -p "Brasil vs. Argentina"
# → "Brasil versus Argentina"
```

## Siglas

```bash
.venv/bin/python tts_ptbr.py -p "Produto com suporte a TTS e IBM"
# → "Produto com suporte a T T S e I B M"

.venv/bin/python tts_ptbr.py -p "Conecte via USB ou API"
# → "Conecte via U S B ou A P I"
```

> Siglas de 1 letra (como "a", "I") não são expandidas.

## Números

```bash
.venv/bin/python tts_ptbr.py -p "São 42 alunos"
# → "São quarenta e dois alunos"

.venv/bin/python tts_ptbr.py -p "Ligou 1.500 vezes"
# → "Ligou mil e quinhentos vezes"

.venv/bin/python tts_ptbr.py -p "Temperatura de 36,7 graus"
# → "Temperatura de trinta e seis vírgula sete graus"
```

## Frase completa mista

```bash
.venv/bin/python tts_ptbr.py -p \
  "Dr. Silva, 3º colocado, ganhou R$ 5.000,00 — uma alta de 12% em relação ao ano anterior."
# → "Doutor Silva, terceiro colocado, ganhou cinco mil reais —
#    uma alta de doze por cento em relação ao ano anterior."
```

## Combinando com batch

```bash
# Arquivo de notas com valores financeiros
.venv/bin/python tts_ptbr.py \
  --preprocessar \
  --arquivo relatorio.txt \
  --salvar relatorio.mp3 \
  --juntar \
  --sem-reproduzir
```

## Via API REST

```bash
curl -s -X POST http://localhost:8080/preprocessar \
  -H "Content-Type: application/json" \
  -d '{"texto": "Dr. Ana ganhou R$ 1.250,00 — 1º lugar"}' \
  | python -m json.tool
```

Resposta:

```json
{
  "original": "Dr. Ana ganhou R$ 1.250,00 — 1º lugar",
  "processado": "Doutora Ana ganhou mil duzentos e cinquenta reais — primeiro lugar"
}
```
