import { readFile, writeFile } from "node:fs/promises";
import process from "node:process";

const mode = process.argv[2] || "sync";
const recordFile = process.env.FEISHU_RECORD_FILE || ".feishu-sync-records.json";

function required(name) {
  const value = process.env[name]?.trim();
  if (!value) throw new Error(`缺少环境变量 ${name}`);
  return value;
}

const config = {
  appId: required("FEISHU_APP_ID"),
  appSecret: required("FEISHU_APP_SECRET"),
  appToken: required("FEISHU_APP_TOKEN"),
  tableId: required("FEISHU_TABLE_ID"),
  viewId: process.env.FEISHU_VIEW_ID?.trim() || "",
  approvedValue: process.env.FEISHU_APPROVED_VALUE?.trim() || "已通过",
  submittedValue: process.env.FEISHU_SUBMITTED_VALUE?.trim() || "已提交审核",
  fields: {
    name: process.env.FEISHU_FIELD_NAME?.trim() || "资源名称",
    url: process.env.FEISHU_FIELD_URL?.trim() || "资源链接",
    description: process.env.FEISHU_FIELD_DESCRIPTION?.trim() || "资源简介",
    category: process.env.FEISHU_FIELD_CATEGORY?.trim() || "内容分类",
    type: process.env.FEISHU_FIELD_TYPE?.trim() || "资源类型",
    tags: process.env.FEISHU_FIELD_TAGS?.trim() || "标签",
    cover: process.env.FEISHU_FIELD_COVER?.trim() || "封面地址",
    review: process.env.FEISHU_FIELD_REVIEW?.trim() || "审核状态",
    sync: process.env.FEISHU_FIELD_SYNC?.trim() || "同步状态",
  },
};

async function getTenantToken() {
  const response = await fetch("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/", {
    method: "POST",
    headers: { "Content-Type": "application/json; charset=utf-8" },
    body: JSON.stringify({ app_id: config.appId, app_secret: config.appSecret }),
  });
  const payload = await response.json();
  if (!response.ok || payload.code !== 0 || !payload.tenant_access_token) {
    throw new Error(`获取飞书访问凭证失败：${payload.msg || response.status}`);
  }
  return payload.tenant_access_token;
}

async function feishuRequest(token, path, options = {}) {
  const response = await fetch(`https://open.feishu.cn/open-apis${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json; charset=utf-8",
      ...options.headers,
    },
  });
  const payload = await response.json();
  if (!response.ok || payload.code !== 0) {
    throw new Error(`飞书接口失败：${payload.msg || response.status}`);
  }
  return payload.data;
}

function textValue(value) {
  if (value == null) return "";
  if (typeof value === "string" || typeof value === "number") return String(value).trim();
  if (Array.isArray(value)) return value.map(textValue).filter(Boolean).join(", ");
  if (typeof value === "object") {
    return textValue(value.text ?? value.name ?? value.link ?? value.url ?? value.value ?? "");
  }
  return "";
}

function urlValue(value) {
  if (Array.isArray(value)) {
    for (const item of value) {
      const result = urlValue(item);
      if (result) return result;
    }
    return "";
  }
  if (value && typeof value === "object") {
    return urlValue(value.link ?? value.url ?? value.text ?? "");
  }
  const match = String(value ?? "").match(/https?:\/\/[^\s，,]+/i);
  return match?.[0] || "";
}

function tagValues(value) {
  if (Array.isArray(value)) return value.map(textValue).filter(Boolean);
  return textValue(value).split(/[,，、]/).map((item) => item.trim()).filter(Boolean);
}

function githubOutput(name, value) {
  if (!process.env.GITHUB_OUTPUT) return;
  return writeFile(process.env.GITHUB_OUTPUT, `${name}=${value}\n`, { flag: "a" });
}

async function listRecords(token) {
  const records = [];
  let pageToken = "";
  do {
    const query = new URLSearchParams({ page_size: "500" });
    if (config.viewId) query.set("view_id", config.viewId);
    if (pageToken) query.set("page_token", pageToken);
    const data = await feishuRequest(
      token,
      `/bitable/v1/apps/${config.appToken}/tables/${config.tableId}/records?${query}`,
    );
    records.push(...(data.items || []));
    pageToken = data.has_more ? data.page_token : "";
  } while (pageToken);
  return records;
}

async function sync(token) {
  const records = await listRecords(token);
  const source = JSON.parse(await readFile("resources.json", "utf8"));
  const existingUrls = new Set(source.resources.map((resource) => resource.url.trim().toLowerCase()));
  const accepted = [];
  const skipped = [];

  for (const record of records) {
    const fields = record.fields || {};
    const review = textValue(fields[config.fields.review]);
    const syncState = textValue(fields[config.fields.sync]);
    if (review !== config.approvedValue || syncState) continue;

    const resource = {
      name: textValue(fields[config.fields.name]),
      description: textValue(fields[config.fields.description]),
      url: urlValue(fields[config.fields.url]),
      category: textValue(fields[config.fields.category]),
      type: textValue(fields[config.fields.type]),
      tags: tagValues(fields[config.fields.tags]),
    };
    const cover = urlValue(fields[config.fields.cover]);
    if (cover) resource.cover = cover;

    const missing = Object.entries(resource)
      .filter(([key, value]) => key !== "tags" && !value)
      .map(([key]) => key);
    if (!resource.tags.length) missing.push("tags");
    if (missing.length) {
      skipped.push(`${record.record_id}: 缺少 ${missing.join(", ")}`);
      continue;
    }
    if (!/^https?:\/\//i.test(resource.url)) {
      skipped.push(`${record.record_id}: 链接格式错误`);
      continue;
    }
    const normalizedUrl = resource.url.trim().toLowerCase();
    if (existingUrls.has(normalizedUrl)) {
      skipped.push(`${record.record_id}: 链接已存在`);
      continue;
    }
    existingUrls.add(normalizedUrl);
    source.resources.push(resource);
    accepted.push({ recordId: record.record_id, name: resource.name, url: resource.url });
  }

  if (skipped.length) console.log(`跳过记录：\n${skipped.join("\n")}`);
  if (!accepted.length) {
    await githubOutput("has_changes", "false");
    await githubOutput("count", "0");
    console.log("没有待同步且审核通过的飞书记录。");
    return;
  }

  const formatter = new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  source.updatedAt = formatter.format(new Date()).replaceAll("/", ".");
  await writeFile("resources.json", `${JSON.stringify(source, null, 2)}\n`, "utf8");
  await writeFile(recordFile, `${JSON.stringify(accepted, null, 2)}\n`, "utf8");
  await githubOutput("has_changes", "true");
  await githubOutput("count", String(accepted.length));
  await githubOutput("names", accepted.map((item) => item.name).join("、"));
  console.log(`已写入 ${accepted.length} 条资源，等待创建 Pull Request。`);
}

async function markSubmitted(token) {
  const records = JSON.parse(await readFile(recordFile, "utf8"));
  const pullRequestUrl = required("PULL_REQUEST_URL");
  for (const record of records) {
    await feishuRequest(
      token,
      `/bitable/v1/apps/${config.appToken}/tables/${config.tableId}/records/${record.recordId}`,
      {
        method: "PUT",
        body: JSON.stringify({
          fields: { [config.fields.sync]: `${config.submittedValue}：${pullRequestUrl}` },
        }),
      },
    );
  }
  console.log(`已回写 ${records.length} 条飞书记录的同步状态。`);
}

const token = await getTenantToken();
if (mode === "sync") await sync(token);
else if (mode === "mark") await markSubmitted(token);
else throw new Error(`未知模式：${mode}`);
