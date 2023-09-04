#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/4 16:12
@Author  : Steven Lee
@File    : mermaid_playwright.py
"""
import os
import asyncio
from metagpt.config import CONFIG
from metagpt.const import PROJECT_ROOT
from metagpt.logs import logger

from urllib.parse import urljoin
from playwright.async_api import async_playwright
import nest_asyncio

__dirname = os.path.dirname(os.path.abspath(__file__))


def mermaid_to_file(mermaid_code, output_file_without_suffix, width=2048, height=2048, output_formats=['png', 'svg', 'pdf']) -> int:
    """
    Converts the given Mermaid code to various output formats and saves them to files.

    Args:
        mermaid_code (str): The Mermaid code to convert.
        output_file_without_suffix (str): The output file name without the file extension.
        width (int, optional): The width of the output image in pixels. Defaults to 2048.
        height (int, optional): The height of the output image in pixels. Defaults to 2048.
        output_formats (list[str], optional): The list of output formats to generate. Defaults to ['png', 'svg', 'pdf'].

    Returns:
        int: Returns 1 if the conversion and saving were successful, -1 otherwise.
    """

    async def mermaid_to_file0(mermaid_code, output_file_without_suffix, width=2048, height=2048, output_formats=['png', 'svg', 'pdf'])-> int:

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            device_scale_factor = 1.0

            context = await browser.new_context(
                    viewport={'width': width, 'height': height},
                    device_scale_factor=device_scale_factor,
                )
            page = await context.new_page()

            async def console_message(msg):
                print(msg.text)
            page.on('console', console_message)

            try:
                await page.set_viewport_size({'width': width, 'height': height})

                mermaid_html_path = os.path.abspath(
                    os.path.join(__dirname, 'index.html'))
                mermaid_html_url = urljoin('file:', mermaid_html_path)
                await page.goto(mermaid_html_url)
                await page.wait_for_load_state("networkidle")

                await page.wait_for_selector("div#container", state="attached")
                mermaid_config = {}
                background_color = "#ffffff"
                my_css = ""
                await page.evaluate(f'document.body.style.background = "{background_color}";')

                metadata = await page.evaluate('''async ([definition, mermaidConfig, myCSS, backgroundColor]) => {
                    const { mermaid, zenuml } = globalThis;
                    await mermaid.registerExternalDiagrams([zenuml]);
                    mermaid.initialize({ startOnLoad: false, ...mermaidConfig });
                    const { svg } = await mermaid.render('my-svg', definition, document.getElementById('container'));
                    document.getElementById('container').innerHTML = svg;
                    const svgElement = document.querySelector('svg');
                    svgElement.style.backgroundColor = backgroundColor;

                    if (myCSS) {
                        const style = document.createElementNS('http://www.w3.org/2000/svg', 'style');
                        style.appendChild(document.createTextNode(myCSS));
                        svgElement.appendChild(style);
                    }

                    let title = null;
                    let desc = null;

                    if (svgElement.firstChild instanceof SVGTitleElement) {
                        title = svgElement.firstChild.textContent;
                    }

                    for (const svgNode of svgElement.children) {
                        if (svgNode instanceof SVGDescElement) {
                            desc = svgNode.textContent;
                            break;
                        }
                    }

                    return {
                        title,
                        desc
                    };
                }''', [mermaid_code, mermaid_config, my_css, background_color])

                if 'svg' in output_formats :
                    svg_xml = await page.evaluate('''() => {
                        const svg = document.querySelector('svg');
                        const xmlSerializer = new XMLSerializer();
                        return xmlSerializer.serializeToString(svg);
                    }''')
                    # result[f'{output_file_without_suffix}.svg'] = svg_xml
                    with open(f'{output_file_without_suffix}.svg', 'wb') as f:
                        f.write(svg_xml.encode('utf-8'))

                if  'png' in output_formats:
                    clip = await page.evaluate('''() => {
                        const svg = document.querySelector('svg');
                        const rect = svg.getBoundingClientRect();
                        return {
                            x: Math.floor(rect.left),
                            y: Math.floor(rect.top),
                            width: Math.ceil(rect.width),
                            height: Math.ceil(rect.height)
                        };
                    }''')
                    await page.set_viewport_size({'width': clip['x'] + clip['width'], 'height': clip['y'] + clip['height']})
                    screenshot = await page.screenshot(clip=clip, omit_background=True, scale='device')
                    with open(f'{output_file_without_suffix}.png', 'wb') as f:
                        f.write(screenshot)
                if 'pdf' in output_formats:
                    pdf_data = await page.pdf(scale=device_scale_factor)
                    with open(f'{output_file_without_suffix}.pdf', 'wb') as f:
                        f.write(pdf_data)
                return 1
            except Exception as e:
                logger.error(e)
                return -1
            finally:
                await browser.close()
    with open(f"{output_file_without_suffix}.mmd", "w", encoding="utf-8") as f:
        f.write(mermaid_code)
    nest_asyncio.apply()
    loop = asyncio.new_event_loop()
    result  = loop.run_until_complete(mermaid_to_file0(mermaid_code, output_file_without_suffix, width, height, output_formats))
    loop.close()
    return result

MMC1 = """classDiagram
    class Main {
        -SearchEngine search_engine
        +main() str
    }
    class SearchEngine {
        -Index index
        -Ranking ranking
        -Summary summary
        +search(query: str) str
    }
    class Index {
        -KnowledgeBase knowledge_base
        +create_index(data: dict)
        +query_index(query: str) list
    }
    class Ranking {
        +rank_results(results: list) list
    }
    class Summary {
        +summarize_results(results: list) str
    }
    class KnowledgeBase {
        +update(data: dict)
        +fetch_data(query: str) dict
    }
    Main --> SearchEngine
    SearchEngine --> Index
    SearchEngine --> Ranking
    SearchEngine --> Summary
    Index --> KnowledgeBase"""

MMC2 = """sequenceDiagram
    participant M as Main
    participant SE as SearchEngine
    participant I as Index
    participant R as Ranking
    participant S as Summary
    participant KB as KnowledgeBase
    M->>SE: search(query)
    SE->>I: query_index(query)
    I->>KB: fetch_data(query)
    KB-->>I: return data
    I-->>SE: return results
    SE->>R: rank_results(results)
    R-->>SE: return ranked_results
    SE->>S: summarize_results(ranked_results)
    S-->>SE: return summary
    SE-->>M: return summary"""


if __name__ == "__main__":
    # logger.info(print_members(print_members))
    mermaid_to_file(MMC1, PROJECT_ROOT / "MMC1")
    mermaid_to_file(MMC2, PROJECT_ROOT / "MMC2")
