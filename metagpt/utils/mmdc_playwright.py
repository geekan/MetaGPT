#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/4 16:12
@Author  : Steven Lee
@File    : mmdc_playwright.py
"""

import os
from urllib.parse import urljoin

from playwright.async_api import async_playwright

from metagpt.logs import logger


async def mermaid_to_file(mermaid_code, output_file_without_suffix, width=2048, height=2048) -> int:
    """
    Converts the given Mermaid code to various output formats and saves them to files.

    Args:
        mermaid_code (str): The Mermaid code to convert.
        output_file_without_suffix (str): The output file name without the file extension.
        width (int, optional): The width of the output image in pixels. Defaults to 2048.
        height (int, optional): The height of the output image in pixels. Defaults to 2048.

    Returns:
        int: Returns 1 if the conversion and saving were successful, -1 otherwise.
    """
    suffixes = ["png", "svg", "pdf"]
    __dirname = os.path.dirname(os.path.abspath(__file__))

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        device_scale_factor = 1.0
        context = await browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=device_scale_factor,
        )
        page = await context.new_page()

        async def console_message(msg):
            logger.info(msg.text)

        page.on("console", console_message)

        try:
            await page.set_viewport_size({"width": width, "height": height})

            mermaid_html_path = os.path.abspath(os.path.join(__dirname, "index.html"))
            mermaid_html_url = urljoin("file:", mermaid_html_path)
            await page.goto(mermaid_html_url)
            await page.wait_for_load_state("networkidle")

            await page.wait_for_selector("div#container", state="attached")
            mermaid_config = {}
            background_color = "#ffffff"
            my_css = ""
            await page.evaluate(f'document.body.style.background = "{background_color}";')

            await page.evaluate(
                """async ([definition, mermaidConfig, myCSS, backgroundColor]) => {
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
            
            }""",
                [mermaid_code, mermaid_config, my_css, background_color],
            )

            if "svg" in suffixes:
                svg_xml = await page.evaluate(
                    """() => {
                    const svg = document.querySelector('svg');
                    const xmlSerializer = new XMLSerializer();
                    return xmlSerializer.serializeToString(svg);
                }"""
                )
                logger.info(f"Generating {output_file_without_suffix}.svg..")
                with open(f"{output_file_without_suffix}.svg", "wb") as f:
                    f.write(svg_xml.encode("utf-8"))

            if "png" in suffixes:
                clip = await page.evaluate(
                    """() => {
                    const svg = document.querySelector('svg');
                    const rect = svg.getBoundingClientRect();
                    return {
                        x: Math.floor(rect.left),
                        y: Math.floor(rect.top),
                        width: Math.ceil(rect.width),
                        height: Math.ceil(rect.height)
                    };
                }"""
                )
                await page.set_viewport_size({"width": clip["x"] + clip["width"], "height": clip["y"] + clip["height"]})
                screenshot = await page.screenshot(clip=clip, omit_background=True, scale="device")
                logger.info(f"Generating {output_file_without_suffix}.png..")
                with open(f"{output_file_without_suffix}.png", "wb") as f:
                    f.write(screenshot)
            if "pdf" in suffixes:
                pdf_data = await page.pdf(scale=device_scale_factor)
                logger.info(f"Generating {output_file_without_suffix}.pdf..")
                with open(f"{output_file_without_suffix}.pdf", "wb") as f:
                    f.write(pdf_data)
            return 0
        except Exception as e:
            logger.error(e)
            return -1
        finally:
            await browser.close()
