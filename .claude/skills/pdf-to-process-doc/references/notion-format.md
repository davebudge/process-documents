# Notion format reference (Process Documentation pages)

Working Notion-flavored markdown for the `update-page` / `create-pages` MCP tools,
confirmed against real pages in the Process Documentation database.

## Destination
- Database: **Process Documentation and Instructions**
  - page URL: https://app.notion.com/p/7a70100a43e64098b71cd6370f1ed398
  - data source id: `a4c0f0f9-6a4b-4d1b-88c9-0032db708e7d`
  - default template: Workshop Manual Template (`23f02a43-0089-80db-9b90-d1d23dfd91d9`)

## Callouts
```
<callout icon="⚠️">
	**Bold lead.** Body text. One tab of indent on the content line.
</callout>
```
Any emoji works as `icon`. Convention icons: `🤖` AI-draft disclaimer (always the
first block), `🔒` confidentiality, `⚠️` safety/verify, `⚡️` HV, `📝` note.
Note: the MCP `fetch` read-back strips the callout background colour even though
it persists on the page — don't trust fetch for colour.

## Headings and steps
```
# Section Heading            (heading_1)
## Step 1: Do the thing      (heading_2 — the uploader matches "Step N:" to place photos)
1. First sub-step.
2. Second sub-step.
```

## Tables
```
<table>
<colgroup><col width="360"><col width="200"><col></colgroup>
<tr><td>Description</td><td>Part number</td><td>Qty</td></tr>
<tr><td>...</td><td>...</td><td>...</td></tr>
</table>
```
`<colgroup>` is optional.

## Checkboxes
```
- [ ] A to-do item
```

## Images and columns
Single image: `![alt](https://public-url/img.jpg)` works only for a **public**
URL. For private uploads use the File Upload API and reference `file-upload://<id>`,
or (as `notion_upload_images.py` does) build the blocks via the raw API:
- image block: `{"type":"image","image":{"type":"file_upload","file_upload":{"id":"<id>"}}}`
- 3-abreast row: a `column_list` with 2-3 `column` children, one image each.
  A `column_list` needs >= 2 columns, so never leave a row of 1 — the uploader
  rebalances (4 -> 2+2, 7 -> 3+2+2, etc.).

## Collapsible table of contents
A `toggle` block containing a `table_of_contents` block:
```
{"type":"toggle","toggle":{
  "rich_text":[{"type":"text","text":{"content":"Table of contents"}}],
  "children":[{"type":"table_of_contents","table_of_contents":{}}]}}
```
The native ToC auto-links every H1/H2 on the page. Place it right after the
first block (the AI-draft callout) so the convention is kept and it's near the top.

## Property values (from the data source schema)
- `Category` (multi_select): `IT - Interior & Trim`, `LV - LV Electrical`,
  `HV - HV Electrical`, `TC - Testing & Calibration`, `WO - WORKSHOP`,
  `BC - Body and Chassis`, `DR - Drivetrain`, `BR - Brakes`,
  `SS - Steering and Suspension`, `HC - Heating Cooling HVAC`,
  `CW - Customer Work and Accessories`, `DC - Dash Controls and Lighting`
- `Category ` (note trailing space, select): `🔋 Battery & Charging`,
  `🧠 System Control`, `⚡️ Motor Transmission & Driveline`, `💧 Thermal Management`,
  `🎛️ Dash & Gauges`, `🪜 Chassis`, `🐚 Body`, `💺 Interior`, `💨 HVAC`,
  `💡 12v Electrical`, `⚙️ Axles`, `🕹️ Steering`, `🧽 Suspension`,
  `🛑 Brakes & Park Brake`, `🛞 Wheels & Tyres`, `🔧 Fasteners`, `🏭 Workshop`,
  `🚗 Projects (PR)`
- `Work Type` (select): `⚡️ New Manufacture`, `🛠 Repair & Rebuild`,
  `👌 Installation & Assembly`, `Modification`
- `In or Out` (select): `Jaunt`, `Jaunt or Partner `, `Fellten`, ... (leave as set)
- `Status` (status): keep `Concept`; `Status ` (select): keep `Draft` until SME review.
