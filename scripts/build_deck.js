const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
pres.author = "Marlon Vargas";
pres.title = "Bussola Publica - Pitch Executivo";

const NAVY = "1E2761";
const NAVY2 = "2E3D74";
const ICE = "CADCFC";
const WHITE = "FFFFFF";
const INK = "1B2435";
const MUTE = "5B6470";
const CORAL = "F96167";
const GREEN = "2E7D32";
const PURPLE = "6A1B9A";
const CARD = "F4F7FC";
const HDR = "Georgia";
const BODY = "Calibri";

const mkShadow = () => ({ type: "outer", color: "1E2761", blur: 8, offset: 3, angle: 135, opacity: 0.12 });

// ---------- Slide 1: Title (dark) ----------
let s = pres.addSlide();
s.background = { color: NAVY };
for (let i = 0; i < 6; i++) {
  s.addShape(pres.shapes.OVAL, { x: 11.2 + (i % 3) * 0.55, y: 0.5 + Math.floor(i / 3) * 0.55, w: 0.28, h: 0.28, fill: { color: ICE, transparency: 60 } });
}
s.addText("PROJETO INTEGRADOR · ENGENHARIA DE DADOS E IA", { x: 0.8, y: 1.5, w: 11, h: 0.4, fontFace: BODY, fontSize: 14, color: ICE, charSpacing: 3, bold: true });
s.addText("Bússola Pública", { x: 0.75, y: 2.0, w: 11.8, h: 1.2, fontFace: HDR, fontSize: 54, color: WHITE, bold: true });
s.addText("Pipeline de Inteligência Legislativa com IA", { x: 0.8, y: 3.25, w: 11.8, h: 0.8, fontFace: HDR, fontSize: 28, color: ICE, italic: true });
s.addText("Da API da Câmara dos Deputados ao radar legislativo que roda sozinho às 06h.", { x: 0.8, y: 4.25, w: 11, h: 0.6, fontFace: BODY, fontSize: 17, color: "AEBBDC" });
const chips = ["Python · Pandas", "Supabase / PostgreSQL", "OpenAI (GPT + Embeddings)", "n8n"];
let cx = 0.8;
chips.forEach(c => {
  const w = 0.35 + c.length * 0.105;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx, y: 5.5, w, h: 0.5, fill: { color: NAVY2 }, line: { color: ICE, width: 1 }, rectRadius: 0.25 });
  s.addText(c, { x: cx, y: 5.5, w, h: 0.5, align: "center", valign: "middle", fontFace: BODY, fontSize: 12, color: WHITE });
  cx += w + 0.25;
});

// ---------- Slide 2: O Problema ----------
s = pres.addSlide();
s.background = { color: WHITE };
s.addText("O problema não é falta de dado.", { x: 0.7, y: 0.5, w: 9, h: 0.7, fontFace: HDR, fontSize: 32, color: NAVY, bold: true });
s.addText("É falta de engenharia de dados.", { x: 0.7, y: 1.15, w: 9, h: 0.6, fontFace: HDR, fontSize: 22, color: CORAL, italic: true });
s.addShape(pres.shapes.RECTANGLE, { x: 9.7, y: 0.55, w: 3.0, h: 1.8, fill: { color: NAVY }, shadow: mkShadow() });
s.addText("R$ 15 mil", { x: 9.7, y: 0.7, w: 3.0, h: 0.7, align: "center", fontFace: HDR, fontSize: 30, color: WHITE, bold: true });
s.addText("por cliente / mês em relatórios feitos à mão por 2 analistas", { x: 9.8, y: 1.4, w: 2.8, h: 0.85, align: "center", fontFace: BODY, fontSize: 12, color: ICE });
const pains = [
  ["Sem base de dados", "Analistas trabalham em planilhas pessoais."],
  ["Sem histórico", "Tudo o que foi consultado se perde."],
  ["Classificação inconsistente", "Cada analista nomeia o tema do seu jeito."],
  ["Alertas por memória", "Se o analista esquece, o cliente é pego de surpresa."],
  ["Nada é medido", "Ninguém sabe volume por tema, partido ou deputado."],
  ["Não escala", "Mais clientes = mais gente lendo o site da Câmara."],
];
let px = 0.7, py = 2.7, cw = 3.9, ch = 1.9, gap = 0.25;
pains.forEach((p, i) => {
  const col = i % 3, row = Math.floor(i / 3);
  const x = px + col * (cw + gap), y = py + row * (ch + gap);
  s.addShape(pres.shapes.RECTANGLE, { x, y, w: cw, h: ch, fill: { color: CARD }, line: { color: "DCE4F2", width: 1 } });
  s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.09, h: ch, fill: { color: CORAL } });
  s.addText(p[0], { x: x + 0.25, y: y + 0.2, w: cw - 0.4, h: 0.55, fontFace: BODY, fontSize: 16, bold: true, color: NAVY });
  s.addText(p[1], { x: x + 0.25, y: y + 0.78, w: cw - 0.45, h: 1.0, fontFace: BODY, fontSize: 13, color: MUTE });
});

// ---------- Slide 3: A Solução (pipeline) ----------
s = pres.addSlide();
s.background = { color: WHITE };
s.addText("A solução: um pipeline de ponta a ponta", { x: 0.7, y: 0.5, w: 12, h: 0.7, fontFace: HDR, fontSize: 30, color: NAVY, bold: true });
s.addText("Captura, organiza, enriquece com IA e entrega — automaticamente.", { x: 0.7, y: 1.15, w: 12, h: 0.5, fontFace: BODY, fontSize: 16, color: MUTE });
const steps = [
  ["1", "Extração", "API da Câmara via requests, paginação e retry. JSON bruto (Bronze).", NAVY],
  ["2", "Transformação", "Pandas: limpeza, dedup, validação de datas e nulos.", NAVY2],
  ["3", "Carga", "Modelo estrela no Supabase via SQLAlchemy.", GREEN],
  ["4", "Camada de IA", "Resumo executivo (GPT) + tema (embeddings).", PURPLE],
  ["5", "Automação", "n8n às 06h + e-mail digest e alerta de falha.", CORAL],
];
let sx = 0.7, sw = 2.32, sgap = 0.18, sy = 2.2, sh = 3.3;
steps.forEach((st, i) => {
  const x = sx + i * (sw + sgap);
  s.addShape(pres.shapes.RECTANGLE, { x, y: sy, w: sw, h: sh, fill: { color: CARD }, line: { color: "DCE4F2", width: 1 }, shadow: mkShadow() });
  s.addShape(pres.shapes.OVAL, { x: x + sw / 2 - 0.42, y: sy + 0.3, w: 0.84, h: 0.84, fill: { color: st[3] } });
  s.addText(st[0], { x: x + sw / 2 - 0.42, y: sy + 0.3, w: 0.84, h: 0.84, align: "center", valign: "middle", fontFace: HDR, fontSize: 28, color: WHITE, bold: true });
  s.addText(st[1], { x: x + 0.1, y: sy + 1.35, w: sw - 0.2, h: 0.5, align: "center", fontFace: BODY, fontSize: 16, bold: true, color: NAVY });
  s.addText(st[2], { x: x + 0.18, y: sy + 1.9, w: sw - 0.36, h: 1.3, align: "center", fontFace: BODY, fontSize: 12, color: MUTE });
  if (i < steps.length - 1) {
    s.addShape(pres.shapes.LINE, { x: x + sw + 0.01, y: sy + sh / 2, w: sgap - 0.02, h: 0, line: { color: MUTE, width: 2, endArrowType: "triangle" } });
  }
});
s.addText("6 tabelas (fato + dimensão) · +30 dias de dados ingeridos · idempotente e resiliente", { x: 0.7, y: 5.9, w: 12, h: 0.5, align: "center", fontFace: BODY, fontSize: 14, italic: true, color: NAVY2 });

// ---------- Slide 4: IA que agrega valor ----------
s = pres.addSlide();
s.background = { color: WHITE };
s.addText("A IA que faz diferença — não decoração", { x: 0.7, y: 0.5, w: 12, h: 0.7, fontFace: HDR, fontSize: 30, color: NAVY, bold: true });
s.addText("O tema e o resumo gerados por IA chegam ao e-mail que o cliente lê.", { x: 0.7, y: 1.15, w: 12, h: 0.5, fontFace: BODY, fontSize: 16, color: MUTE });
const colY = 2.05, colH = 2.9, colW = 5.9;
s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: colY, w: colW, h: colH, fill: { color: CARD }, line: { color: "DCE4F2", width: 1 }, shadow: mkShadow() });
s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: colY, w: colW, h: 0.7, fill: { color: PURPLE } });
s.addText("Resumo executivo  ·  GPT-4o-mini", { x: 0.9, y: colY, w: colW - 0.4, h: 0.7, valign: "middle", fontFace: BODY, fontSize: 17, bold: true, color: WHITE });
s.addText([
  { text: "Ementa técnica → 3 frases claras para executivos.", options: { bullet: true, breakLine: true } },
  { text: "Estrutura: o que propõe · quem é impactado · ponto de atenção.", options: { bullet: true, breakLine: true } },
  { text: "Grava resumo_executivo em fato_proposicoes.", options: { bullet: true } },
], { x: 0.95, y: colY + 0.9, w: colW - 0.6, h: colH - 1.0, fontFace: BODY, fontSize: 14, color: INK, paraSpaceAfter: 8 });
s.addShape(pres.shapes.RECTANGLE, { x: 6.9, y: colY, w: colW, h: colH, fill: { color: CARD }, line: { color: "DCE4F2", width: 1 }, shadow: mkShadow() });
s.addShape(pres.shapes.RECTANGLE, { x: 6.9, y: colY, w: colW, h: 0.7, fill: { color: GREEN } });
s.addText("Classificação temática  ·  Embeddings", { x: 7.1, y: colY, w: colW - 0.4, h: 0.7, valign: "middle", fontFace: BODY, fontSize: 17, bold: true, color: WHITE });
s.addText([
  { text: "text-embedding-3-small + similaridade de cosseno.", options: { bullet: true, breakLine: true } },
  { text: "11 temas controlados (Tecnologia, Saúde, Tributário…).", options: { bullet: true, breakLine: true } },
  { text: "Grava tema + tema_score (auditável) em fato_proposicoes.", options: { bullet: true } },
], { x: 7.15, y: colY + 0.9, w: colW - 0.6, h: colH - 1.0, fontFace: BODY, fontSize: 14, color: INK, paraSpaceAfter: 8 });
s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 5.2, w: 12.1, h: 1.55, fill: { color: NAVY } });
s.addText("Custo sob controle", { x: 0.95, y: 5.35, w: 4, h: 0.5, fontFace: BODY, fontSize: 16, bold: true, color: ICE });
s.addText([
  { text: "DRY_RUN", options: { bold: true, color: ICE } },
  { text: " por padrão: estima tokens e custo (USD/BRL) antes de gastar. Classificar 1.000 proposições por embeddings custa poucos centavos de real.", options: { color: WHITE } },
], { x: 0.95, y: 5.8, w: 11.6, h: 0.85, fontFace: BODY, fontSize: 14 });

// ---------- Slide 5: Automação / Demo ----------
s = pres.addSlide();
s.background = { color: WHITE };
s.addText("Roda sozinho às 06h", { x: 0.7, y: 0.5, w: 9, h: 0.7, fontFace: HDR, fontSize: 30, color: NAVY, bold: true });
s.addText("Workflow n8n: agenda → pipeline → consulta → e-mail. Com tratamento de falha.", { x: 0.7, y: 1.15, w: 12, h: 0.5, fontFace: BODY, fontSize: 16, color: MUTE });
const flow = [
  ["Schedule 06h", "cron 0 6 * * *", NAVY],
  ["Execute Command", "poetry run python main.py", NAVY2],
  ["Pipeline OK?", "checa exitCode", "C28800"],
  ["Postgres do dia", "top 5 + tema + resumo", GREEN],
  ["E-mail digest", "radar legislativo", PURPLE],
];
let fx = 0.7, fw = 2.32, fgap = 0.18, fy = 2.2, fh = 1.5;
flow.forEach((f, i) => {
  const x = fx + i * (fw + fgap);
  s.addShape(pres.shapes.RECTANGLE, { x, y: fy, w: fw, h: fh, fill: { color: f[2] }, shadow: mkShadow() });
  s.addText(f[0], { x: x + 0.1, y: fy + 0.28, w: fw - 0.2, h: 0.5, align: "center", fontFace: BODY, fontSize: 14, bold: true, color: WHITE });
  s.addText(f[1], { x: x + 0.1, y: fy + 0.82, w: fw - 0.2, h: 0.5, align: "center", fontFace: BODY, fontSize: 11, color: "E8EEFA" });
  if (i < flow.length - 1) s.addShape(pres.shapes.LINE, { x: x + fw + 0.01, y: fy + fh / 2, w: fgap - 0.02, h: 0, line: { color: MUTE, width: 2, endArrowType: "triangle" } });
});
s.addShape(pres.shapes.RECTANGLE, { x: 5.5, y: 4.05, w: 2.32, h: 0.85, fill: { color: CORAL } });
s.addText("Falha → alerta", { x: 5.5, y: 4.05, w: 2.32, h: 0.85, align: "center", valign: "middle", fontFace: BODY, fontSize: 13, bold: true, color: WHITE });
s.addShape(pres.shapes.LINE, { x: 5.78, y: 3.7, w: 0, h: 0.34, line: { color: CORAL, width: 2, endArrowType: "triangle" } });
s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 5.25, w: 12.1, h: 1.5, fill: { color: CARD }, line: { color: "DCE4F2", width: 1 } });
s.addText("O que chega ao cliente, todo dia, sem ninguém olhando:", { x: 0.95, y: 5.4, w: 11.5, h: 0.45, fontFace: BODY, fontSize: 15, bold: true, color: NAVY });
s.addText([
  { text: "As 5 proposições mais relevantes das últimas 24h  ·  ", options: {} },
  { text: "tema (IA)  ·  ", options: { color: GREEN, bold: true } },
  { text: "resumo executivo (IA)  ·  ", options: { color: PURPLE, bold: true } },
  { text: "alerta imediato se o pipeline quebrar.", options: { color: CORAL, bold: true } },
], { x: 0.95, y: 5.9, w: 11.6, h: 0.7, fontFace: BODY, fontSize: 14, color: INK });
s.addText("Demo na entrega: print da execução no n8n · e-mail recebido · coluna tema no Supabase.", { x: 0.95, y: 6.45, w: 11.6, h: 0.35, fontFace: BODY, fontSize: 11, italic: true, color: MUTE });

// ---------- Slide 6: Próximos passos (dark) ----------
s = pres.addSlide();
s.background = { color: NAVY };
s.addText("Próximos passos", { x: 0.8, y: 0.7, w: 11, h: 0.8, fontFace: HDR, fontSize: 34, color: WHITE, bold: true });
const next = [
  ["Alerta por tema crítico", "Disparo Telegram/e-mail quando entra proposição de Tecnologia ou outro tema do cliente."],
  ["Dashboard de BI", "Volume por tema, partido mais ativo e deputado mais produtivo (Power BI sobre o Supabase)."],
  ["Janela histórica", "Ampliar de 30 dias para múltiplos anos, com carga incremental."],
  ["Produto multicliente", "Catálogo de temas e destinatários por cliente — o relatório de R$ 15 mil, automatizado."],
];
let ny = 1.9;
next.forEach((n, i) => {
  const y = ny + i * 1.18;
  s.addShape(pres.shapes.OVAL, { x: 0.9, y, w: 0.55, h: 0.55, fill: { color: ICE } });
  s.addText(String(i + 1), { x: 0.9, y, w: 0.55, h: 0.55, align: "center", valign: "middle", fontFace: HDR, fontSize: 20, bold: true, color: NAVY });
  s.addText(n[0], { x: 1.7, y: y - 0.05, w: 10.8, h: 0.5, fontFace: BODY, fontSize: 18, bold: true, color: WHITE });
  s.addText(n[1], { x: 1.7, y: y + 0.42, w: 10.8, h: 0.6, fontFace: BODY, fontSize: 13, color: "AEBBDC" });
});
s.addText("Encare como se a Bússola Pública existisse de verdade — porque, no fim, vai estar.", { x: 0.8, y: 6.75, w: 11.8, h: 0.5, align: "center", fontFace: HDR, fontSize: 15, italic: true, color: ICE });

pres.writeFile({ fileName: "Bussola_Publica_Pitch.pptx" }).then(f => console.log("OK:", f));
