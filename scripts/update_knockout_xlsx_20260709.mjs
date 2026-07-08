import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "2026世界杯淘汰赛赛程表_中文版_Codex.xlsx";
const outputPath = inputPath;
const qaDir = "data/xlsx_qa";

await fs.mkdir(qaDir, { recursive: true });

const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const sheet = workbook.worksheets.getItem("淘汰赛赛程");

const before = await workbook.render({
  sheetName: "淘汰赛赛程",
  range: "A23:Z30",
  scale: 1,
  format: "png",
});
await fs.writeFile(`${qaDir}/knockout_rows_23_30_20260709_before.png`, new Uint8Array(await before.arrayBuffer()));

const updates = [
  { row: 24, home: ["阿根廷", "Argentina", "ARG"], away: ["埃及", "Egypt", "EGY"], status: "已完赛：阿根廷3-2晋级" },
  { row: 25, home: ["瑞士", "Switzerland", "SUI"], away: ["哥伦比亚", "Colombia", "COL"], status: "已完赛：瑞士0-0，点球4-1晋级" },
  { row: 26, home: ["法国", "France", "FRA"], away: ["摩洛哥", "Morocco", "MAR"], status: "未开赛" },
  { row: 27, home: ["西班牙", "Spain", "ESP"], away: ["比利时", "Belgium", "BEL"], status: "未开赛" },
  { row: 28, home: ["挪威", "Norway", "NOR"], away: ["英格兰", "England", "ENG"], status: "未开赛" },
  { row: 29, home: ["阿根廷", "Argentina", "ARG"], away: ["瑞士", "Switzerland", "SUI"], status: "未开赛" },
];

for (const item of updates) {
  sheet.getRange(`E${item.row}:J${item.row}`).values = [[
    item.home[0],
    item.home[1],
    item.home[2],
    item.away[0],
    item.away[1],
    item.away[2],
  ]];
  sheet.getRange(`U${item.row}`).values = [[item.status]];
}

sheet.getRange("Y1:Z1").values = [["最近更新", "2026-07-09：回填95-96赛果，100更新为阿根廷 vs 瑞士，生成97-100预测"]];

const check = await workbook.inspect({
  kind: "region",
  sheetId: "淘汰赛赛程",
  range: "A23:Z30",
  maxChars: 10000,
});
console.log(check.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "formula error scan",
});
console.log(errors.ndjson);

const after = await workbook.render({
  sheetName: "淘汰赛赛程",
  range: "A23:Z30",
  scale: 1,
  format: "png",
});
await fs.writeFile(`${qaDir}/knockout_rows_23_30_20260709_after.png`, new Uint8Array(await after.arrayBuffer()));

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`Saved ${outputPath}`);
