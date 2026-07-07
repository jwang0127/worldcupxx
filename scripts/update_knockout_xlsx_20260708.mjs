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
  range: "A20:X29",
  scale: 1,
  format: "png",
});
await fs.writeFile(`${qaDir}/knockout_rows_20_29_before.png`, new Uint8Array(await before.arrayBuffer()));

const updates = [
  { row: 20, home: ["巴西", "Brazil", "BRA"], away: ["挪威", "Norway", "NOR"], status: "已完赛：挪威1-2晋级" },
  { row: 21, home: ["墨西哥", "Mexico", "MEX"], away: ["英格兰", "England", "ENG"], status: "已完赛：英格兰2-3晋级" },
  { row: 22, home: ["葡萄牙", "Portugal", "POR"], away: ["西班牙", "Spain", "ESP"], status: "已完赛：西班牙0-1晋级" },
  { row: 23, home: ["美国", "United States", "USA"], away: ["比利时", "Belgium", "BEL"], status: "已完赛：比利时1-4晋级" },
  { row: 24, home: ["阿根廷", "Argentina", "ARG"], away: ["埃及", "Egypt", "EGY"], status: "未开赛" },
  { row: 25, home: ["瑞士", "Switzerland", "SUI"], away: ["哥伦比亚", "Colombia", "COL"], status: "未开赛" },
  { row: 26, home: ["法国", "France", "FRA"], away: ["摩洛哥", "Morocco", "MAR"], status: "未开赛" },
  { row: 27, home: ["西班牙", "Spain", "ESP"], away: ["比利时", "Belgium", "BEL"], status: "未开赛" },
  { row: 28, home: ["挪威", "Norway", "NOR"], away: ["英格兰", "England", "ENG"], status: "未开赛" },
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

sheet.getRange("Y1:Z1").values = [["最近更新", "2026-07-07：回填91-94赛果、95-99已确定对阵"]];

const check = await workbook.inspect({
  kind: "region",
  sheetId: "淘汰赛赛程",
  range: "A20:Z29",
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
  range: "A20:Z29",
  scale: 1,
  format: "png",
});
await fs.writeFile(`${qaDir}/knockout_rows_20_29_after.png`, new Uint8Array(await after.arrayBuffer()));

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`Saved ${outputPath}`);
