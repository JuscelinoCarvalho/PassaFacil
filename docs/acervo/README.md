# Acervo — ingestão das imagens de estudo (`novas/`)

Pipeline para transformar as 64 imagens JPG em `novas/` (questões, capas, estudos
de caso, leis, pegadinhas) em conteúdo do sistema, **sem risco de quebra de sessão**:
o estado vive em disco (git), não na memória da conversa.

## Fluxo

1. **Leitura em lotes** (~6 imagens/turno, agrupadas por família). Cada imagem lida
   vira um `ingest/raw/<nome>.json` (transcrição literal + classificação + campos
   extraídos) e é marcada `done` em `ingest/_manifest.json` (checkpoint). Se a
   sessão cair/comprimir, o manifesto diz de onde retomar.
> ⚠️ **Variantes "b" (ex.: `quest5b`, `qUEST1b`):** NÃO são sempre duplicatas.
> Algumas são a **continuação** da mesma questão (2ª parte/enunciado que segue),
> outras são cópias. Sempre comparar o "b" com a base antes de decidir: se for
> continuação, **juntar** os dois numa só questão; se for cópia, marcar `skipped`
> (dedup). Registrado após `quest2bRaciocinio` (cópia) vs. caso de continuação
> apontado pelo dono.

2. **Consolidação:** os `raw/*.json` de questões viram `questoes/<materia>.json`
   (payload do `POST /question-bank/import`); os de leis viram `leis/<norma>.md`
   + `.json`; estudos de caso viram registros de `DiscursiveCase`.
3. **Aplicação no banco:** `apps/api/scripts/importar_acervo.py` (idempotente,
   dedup por `content_hash`) grava em produção — passo final, aprovado pelo dono.
   Questões entram **não publicadas** (`owner_only`) para revisão.

## Pastas

| Caminho | Conteúdo |
|---|---|
| `ingest/_manifest.json` | Checkpoint: cada arquivo → categoria, status, hash |
| `ingest/raw/<nome>.json` | 1 por imagem: transcrição + classificação |
| `questoes/<materia>.json` | Lotes prontos para importar (dedup no servidor) |
| `leis/<norma>.md` / `.json` | Acervo de leis (ver schema abaixo) |
| `observacoes/padroes.md` | Como cada assunto é cobrado + dificuldade |
| `observacoes/insumos_faltantes.md` | O que buscar depois p/ completar micro-aulas |

## Schema do acervo de leis (`leis/*.json`)

Registro-base para o **futuro módulo "decorar leis" (não os artigos)** — macro-resumos
que ajudam nas discursivas. Ainda **não** vira tabela no banco (decisão: por ora só
acervo em git). Campos:

```json
{
  "norma": "Constituição Federal de 1988",
  "dispositivo": "art. 71",
  "apelido": "DNA do Controle Externo",
  "ambito": "federal | estadual",
  "assunto": "Competências do Tribunal de Contas",
  "macro_resumo": "Ideia central em 2-4 frases, para memorizar (não decorar o texto do artigo).",
  "palavras_chave": ["controle externo", "auxílio ao legislativo"],
  "conexoes": ["art. 70", "art. 75"],
  "pegadinhas": ["confundir sustar contrato (Congresso) x sustar ato (TCU)"],
  "para_discursiva": "Como acionar este dispositivo numa resposta de estudo de caso.",
  "fonte_imagem": "art71.jpg"
}
```

> Próxima fase (registrada, fora deste passo): criar tópicos/tabela para todas as
> leis do edital e um módulo de memorização — ver `observacoes/padroes.md`.
