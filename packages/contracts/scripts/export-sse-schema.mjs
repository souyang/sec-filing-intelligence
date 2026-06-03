import { spawnSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");
const out = join(dirname(fileURLToPath(import.meta.url)), "../sse-events.schema.json");

const result = spawnSync(
  "uv",
  ["run", "python", "-c", "from sec_alphaops_common.events.sse import export_sse_json_schema; import json; print(json.dumps(export_sse_json_schema()))"],
  { cwd: root, encoding: "utf-8" },
);

if (result.status !== 0) {
  console.error(result.stderr || result.stdout);
  process.exit(result.status ?? 1);
}

writeFileSync(out, JSON.stringify(JSON.parse(result.stdout.trim()), null, 2) + "\n");
console.log(`Wrote ${out}`);
