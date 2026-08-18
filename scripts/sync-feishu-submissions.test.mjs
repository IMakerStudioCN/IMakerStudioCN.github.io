import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

test("latest mode skips an incomplete record and syncs the next valid record", async () => {
  const directory = await mkdtemp(join(tmpdir(), "feishu-sync-"));
  const originalDirectory = process.cwd();
  const requestedUrls = [];

  try {
    process.chdir(directory);
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
              created_time: "1787068800000",
              fields: {
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
              created_time: "1786982400000",
              fields: {
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
  } finally {
    process.chdir(originalDirectory);
    await rm(directory, { recursive: true, force: true });
  }
});
