import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

test("latest mode skips an incomplete record and syncs the next valid record", async () => {
  const directory = await mkdtemp(join(tmpdir(), "feishu-sync-"));
  const originalDirectory = process.cwd();
  const originalConsoleLog = console.log;
  const requestedUrls = [];
  const logs = [];

  try {
    process.chdir(directory);
    console.log = (...values) => logs.push(values.join(" "));
    await writeFile("resources.json", `${JSON.stringify({ updatedAt: "", resources: [] })}\n`);

    Object.assign(process.env, {
      FEISHU_APP_ID: "test-app",
      FEISHU_APP_SECRET: "test-secret",
      FEISHU_APP_TOKEN: "test-token",
      FEISHU_TABLE_ID: "test-table",
      FEISHU_SYNC_MODE: "latest",
      GITHUB_OUTPUT: join(directory, "github-output.txt"),
    });

    globalThis.fetch = async (url) => {
      requestedUrls.push(String(url));
      if (String(url).includes("tenant_access_token")) {
        return Response.json({ code: 0, tenant_access_token: "tenant-token" });
      }
      return Response.json({
        code: 0,
        data: {
          has_more: false,
          items: [
            {
              record_id: "newest-incomplete",
              fields: {
                投稿时间: "1787068800000",
                资源名称: "缺少简介",
                资源链接: "https://example.com/incomplete",
                内容分类: "工具",
                资源类型: "网站",
                标签: ["测试"],
                审核状态: "已通过",
              },
            },
            {
              record_id: "older-valid",
              fields: {
                投稿时间: "1786982400000",
                资源名称: "有效资源",
                资源简介: "完整简介",
                资源链接: "https://example.com/valid",
                内容分类: "工具",
                资源类型: "网站",
                标签: ["测试"],
                审核状态: "已通过",
              },
            },
          ],
        },
      });
    };

    await import(`./sync-feishu-submissions.mjs?test=${Date.now()}`);

    const source = JSON.parse(await readFile("resources.json", "utf8"));
    assert.equal(source.resources.length, 1);
    assert.equal(source.resources[0].name, "有效资源");
    assert.equal(source.resources[0].url, "https://example.com/valid");
    assert.match(await readFile(process.env.GITHUB_OUTPUT, "utf8"), /has_changes=true/);
    assert.ok(requestedUrls.some((url) => url.includes("with_automatic_fields=true")));
    assert.ok(logs.some((line) => line.includes("本次同步投稿：有效资源（飞书记录 ID：older-valid）")));
    assert.ok(logs.some((line) => line.includes("投稿时间：2026/08/18 00:00:00")));
    assert.ok(logs.some((line) => line.includes("缺少简介（飞书记录 ID：newest-incomplete）：缺少 资源简介")));
  } finally {
    console.log = originalConsoleLog;
    process.chdir(originalDirectory);
    await rm(directory, { recursive: true, force: true });
  }
});

test("batch synchronization is the default", async () => {
  const script = await readFile(new URL("./sync-feishu-submissions.mjs", import.meta.url), "utf8");
  const workflow = await readFile(new URL("../.github/workflows/sync-feishu-submissions.yml", import.meta.url), "utf8");

  assert.match(script, /FEISHU_SYNC_MODE\?\.trim\(\)\.toLowerCase\(\) \|\| "all"/);
  assert.match(workflow, /FEISHU_SYNC_MODE: \$\{\{ vars\.FEISHU_SYNC_MODE \|\| 'all' \}\}/);
});

test("workflow automatically merges Feishu pull requests with the dedicated token", async () => {
  const workflow = await readFile(new URL("../.github/workflows/sync-feishu-submissions.yml", import.meta.url), "utf8");

  assert.doesNotMatch(workflow, /--draft/);
  assert.equal(workflow.match(/secrets\.FEISHU_MERGE_TOKEN/g)?.length, 2);
  assert.match(workflow, /gh pr merge "\$\{\{ steps\.pull_request\.outputs\.url \}\}" --merge --delete-branch/);
  assert.ok(workflow.indexOf("Mark Feishu records as submitted") < workflow.indexOf("Merge pull request"));
});
