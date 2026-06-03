import { execSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const contractsDir = join(dirname(fileURLToPath(import.meta.url)), "..");

if (!existsSync(join(contractsDir, "sse-events.schema.json"))) {
  console.error("Missing sse-events.schema.json — run pnpm generate:contracts");
  process.exit(1);
}

try {
  execSync("git diff --exit-code sse-events.schema.json api.d.ts", {
    cwd: contractsDir,
    stdio: "inherit",
  });
  console.log("Contract artifacts are up to date.");
} catch {
  console.error("Contract drift detected. Run: pnpm generate:contracts");
  process.exit(1);
}
