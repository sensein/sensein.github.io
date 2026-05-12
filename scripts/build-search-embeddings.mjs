#!/usr/bin/env node
/**
 * Build-time MiniLM embeddings for the cross-site search.
 *
 * Walks the same data files as src/pages/search.astro (people, projects,
 * publications), builds the same record-text strings, encodes each with
 * `Xenova/all-MiniLM-L6-v2` (384 dims), normalises to unit length, and
 * writes:
 *
 *   public/search-vectors.bin
 *     16-byte header: "SVEC" + uint32 count + uint32 dim + uint32 dtype(2)
 *     then count × dim Float16 (Uint16) little-endian values.
 *
 *   public/search-index.json
 *     Array of { k, t, b, h, y, g, r, s } in EXACTLY the same order as
 *     the binary. The runtime fetches both and uses them in parallel.
 *
 * The search page can fall back to keyword-only scoring if the vectors
 * file is missing — semantic ranking is an enhancement, not a hard
 * dependency.
 */
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import yaml from "js-yaml";
import { pipeline, env } from "@xenova/transformers";

env.allowLocalModels = false;
env.useFSCache = true;

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DATA = path.join(ROOT, "src", "data");

async function readYaml(name) {
  const text = await fs.readFile(path.join(DATA, name), "utf-8");
  return yaml.load(text);
}

function personSlug(name) {
  return name
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

async function buildRecords() {
  const records = [];

  const team = (await readYaml("team_members.yml")) ?? [];
  for (const m of team) {
    records.push({
      k: "person",
      t: m.name,
      b: `${m.info ?? ""} ${m.email ?? ""}`,
      h: `/team/#${personSlug(m.name)}`,
      y: null,
      g: ["current"].join(","),
      r: "current",
      s: null,
    });
  }
  const studs = (await readYaml("students.yml")) ?? [];
  for (const m of studs) {
    records.push({
      k: "person",
      t: m.name,
      b: `${m.info ?? ""} ${m.email ?? ""}`,
      h: `/team/#${personSlug(m.name)}`,
      y: null,
      g: ["students"].join(","),
      r: "students",
      s: null,
    });
  }
  const alums = (await readYaml("alumni_members.yml")) ?? [];
  for (const m of alums) {
    records.push({
      k: "person",
      t: m.name,
      b: `${m.info ?? ""} ${m.duration ?? ""}`,
      h: `/team/#${personSlug(m.name)}`,
      y: null,
      g: ["alumni"].join(","),
      r: "alumni",
      s: null,
    });
  }
  const projs = (await readYaml("projects.yml")) ?? [];
  for (const p of projs) {
    records.push({
      k: "project",
      t: p.title,
      b: `${p.description ?? ""} ${p.funder ?? ""} ${(p.contributors?.current ?? []).join(" ")} ${(p.contributors?.former ?? []).join(" ")}`,
      h: `/projects/${p.slug}`,
      y: null,
      g: (p.themes ?? []).join(","),
      r: null,
      s: p.status ?? null,
    });
  }
  const pubs = (await readYaml("publications.yml")) ?? [];
  for (const pub of pubs) {
    records.push({
      k: "publication",
      t: pub.title,
      b: `${(pub.authors ?? []).join(", ")} ${pub.venue ?? ""}`,
      h: `/publications/${pub.id}`,
      y: pub.year ?? null,
      g: (pub.topics ?? []).join(","),
      r: null,
      s: null,
    });
  }
  return records;
}

function textFor(r) {
  // Concatenate the meaningful fields. Keep it short to fit MiniLM's
  // 256-token sequence cap comfortably.
  return [r.t, r.b, r.g].filter(Boolean).join(" · ").slice(0, 1500);
}

// Float32 → IEEE 754 binary16 conversion (lossy, fine for cosine sim).
function f32ToF16(val) {
  const f32 = new Float32Array([val]);
  const u32 = new Uint32Array(f32.buffer)[0];
  const sign = (u32 >> 16) & 0x8000;
  let mant = u32 & 0x7fffff;
  let exp = (u32 >> 23) & 0xff;
  if (exp === 255) return sign | 0x7c00 | (mant ? 0x200 : 0); // Inf / NaN
  exp -= 112; // 127 (f32 bias) - 15 (f16 bias) = 112
  if (exp <= 0) {
    if (exp < -10) return sign;
    mant = (mant | 0x800000) >> (1 - exp);
    if (mant & 0x1000) mant += 0x2000;
    return sign | (mant >> 13);
  }
  if (exp >= 31) return sign | 0x7c00; // overflow → Inf
  if (mant & 0x1000) {
    mant += 0x2000;
    if (mant & 0x800000) { mant = 0; exp += 1; }
    if (exp >= 31) return sign | 0x7c00;
  }
  return sign | (exp << 10) | (mant >> 13);
}

async function main() {
  console.log("Loading model: Xenova/all-MiniLM-L6-v2");
  const extractor = await pipeline("feature-extraction", "Xenova/all-MiniLM-L6-v2");
  const records = await buildRecords();
  console.log(`Encoding ${records.length} records…`);

  const dim = 384;
  const buf = Buffer.alloc(16 + records.length * dim * 2);
  buf.write("SVEC", 0, "ascii");
  buf.writeUInt32LE(records.length, 4);
  buf.writeUInt32LE(dim, 8);
  buf.writeUInt32LE(2, 12); // dtype: 2 = float16

  let written = 0;
  for (let i = 0; i < records.length; i++) {
    const text = textFor(records[i]);
    const output = await extractor(text, { pooling: "mean", normalize: true });
    const arr = output.data;
    if (arr.length !== dim) throw new Error(`Unexpected dim ${arr.length} for record ${i}`);
    for (let j = 0; j < dim; j++) {
      buf.writeUInt16LE(f32ToF16(arr[j]), 16 + (i * dim + j) * 2);
    }
    written++;
    if (written % 25 === 0) console.log(`  ${written}/${records.length}`);
  }

  await fs.mkdir(path.join(ROOT, "public"), { recursive: true });
  await fs.writeFile(path.join(ROOT, "public", "search-vectors.bin"), buf);
  await fs.writeFile(
    path.join(ROOT, "public", "search-index.json"),
    JSON.stringify(records),
  );
  console.log(`Wrote ${buf.length} bytes to public/search-vectors.bin`);
  console.log(`Wrote ${records.length} records to public/search-index.json`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
