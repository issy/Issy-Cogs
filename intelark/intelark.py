import re
from typing import List, Tuple

import aiohttp
import bs4
import discord
from bs4 import BeautifulSoup as soup
from redbot.core import commands
from redbot.core.utils.menus import close_menu, menu, next_page, prev_page

CUSTOM_CONTROLS = {"⬅️": prev_page, "⏹️": close_menu, "➡️": next_page}

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"
}

__author__ = "Issy"

desired_specs = (
    "ProcessorNumber",
    "CoreCount",
    "ThreadCount",
    "HyperThreading",
    "ClockSpeed",
    "SocketsSupported",
    "MaxTDP",
    "AESTech",
    "MaxMem",
)
returned_specs = (
    "Url",
    "ProcessorNumber",
    "CoreCount",
    "ThreadCount",
    "HyperThreading",
    "ClockSpeed",
    "SocketsSupported",
    "MaxTDP",
    "AESTech",
    "MaxMem",
    "VTD",
    "ClockSpeedMax",
)
ignore_words = (
    "generation",
    "ethernet",
    "wireless",
    "products formerly",
    "heat sink",
    "compute module",
    "board",
)


async def make_soup(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, allow_redirects=True) as data:
            data_text = await data.text()
            page_soup = soup(data_text, "html.parser")
            await session.close()
    return page_soup


class IntelArk(commands.Cog):
    """Search for Intel CPUs"""

    def __init__(self, client):
        self.client = client
        self.intel_blue = 0x0071C5

    # Commands

    @commands.command(name="ark")
    async def _ark(self, ctx, *, search_term: str):
        """Search for Intel CPUs"""
        # Check for special queries
        async with ctx.channel.typing():
            response = self.get_response(ctx, search_term)
            if response:
                await ctx.send(embed=response)
                return

            results: Tuple[discord.Embed] = await self.get_search_results(search_term)
            if not results:
                embed = discord.Embed(
                    description=f"No results found for `{search_term.replace('`','``')}`",
                    colour=self.intel_blue,
                )
                await ctx.send(embed=embed)
                return
            if len(results) == 1:
                await ctx.send(embed=results[0])
                return
        await menu(
            ctx,
            pages=results,
            controls=CUSTOM_CONTROLS,
            message=None,
            page=0,
            timeout=120,
        )

    # Helper functions

    def get_response(self, ctx, search_term: str) -> discord.Embed:
        """Get quirky responses for special triggers"""
        special_queries = {
            "@everyone": "Hah. Nice try. Being very funny. Cheeky cunt.",
            "@here": "Hilarious, I'm reporting you to the mods.",
            ":(){ :|: & };: -": "This is a python bot, not a bash bot you nimwit.",
        }
        for word in search_term.split(" "):
            if word in special_queries:
                return discord.Embed(colour=self.intel_blue, description=special_queries[word])
            if re.compile("<@![0-9]{18}>").match(word):
                return discord.Embed(colour=self.intel_blue, description=f"<@{ctx.author.id}> pong!")
        return False

    def get_urls(self, page_soup: soup) -> Tuple[str]:
        if page_soup.find("input", {"id": "FormRedirectUrl"}):  # if only one result
            url = page_soup.find("input", {"id": "FormRedirectUrl"}).get("value")
            return f"https://ark.intel.com{url}"
        if page_soup.find("h2", text="No products matching your request were found."):  # if no products found
            return ()
        # build list of URLs
        results = page_soup.findAll("div", {"class": "search-result"})
        urls = [
            f"""https://ark.intel.com{i.find("h4",{"class":"result-title"}).find("a")['href']}"""
            for i in results
            if self.check_product_title(i)
        ]
        for item in results:
            trigger = False
            item_title = item.find("h4", {"class": "result-title"}).find("a").contents[0].strip().lower()
            # If certain keywords are in the product title, skip this product
            for word in ignore_words:
                if word in item_title:
                    trigger = True
            if not trigger:
                url_suffix = item.find("h4", {"class": "result-title"}).find("a").get("href")
                url = f"https://ark.intel.com{url_suffix}"
                urls.append(url)
        return tuple(urls)

    def check_product_title(self, product: bs4.element.Tag) -> bool:
        item_title = item.find("h4", {"class": "result-title"}).find("a").contents[0].strip().lower()
        for word in ignore_words:
            if word in item_title:
                return False
        return True

    def get_cpu_data(self, page: soup) -> dict:
        specs = {}
        specs["Url"] = page.find("meta", {"property": "og:url"})["content"]
        for spec_item in desired_specs:
            try:
                specs[spec_item] = page.find("span", {"class": "value", "data-key": spec_item}).contents[0].strip()
            except AttributeError:
                specs[spec_item] = None
        for spec_item in ["VTD", "ClockSpeedMax"]:
            try:
                specs[spec_item] = page.find("span", {"class": "value", "data-key": spec_item}).contents[0].strip()
            except AttributeError:
                specs[spec_item] = None
        return specs

    def make_ark_embed(self, data: dict, index: dict = {}) -> discord.Embed:
        embed = discord.Embed(title="Ark Search Result", url=data["Url"], colour=self.intel_blue)
        embed.add_field(
            name="Product Name",
            value=f"[{data['ProcessorNumber']}]({data['Url']})",
            inline=True,
        )
        if data["ClockSpeed"] != None:
            if data["ClockSpeedMax"] != None:
                embed.add_field(
                    name="Clock Speed",
                    value=f"{data['ClockSpeed']} / {data['ClockSpeedMax']}",
                    inline=True,
                )
            else:
                embed.add_field(name="Clock Speed", value=data["ClockSpeed"], inline=True)
        core_thread_value = (
            f"{data['CoreCount']} / {data['CoreCount']}"
            if data["HyperThreading"] == "No" or data["HyperThreading"] == None
            else f"{data['CoreCount']} / {data['ThreadCount']}"
        )
        embed.add_field(name="Cores/Threads", value=core_thread_value, inline=True)
        if data["MaxTDP"] != None:
            embed.add_field(name="TDP", value=data["MaxTDP"], inline=True)
        if data["VTD"] != None:
            embed.add_field(name="VTD", value=data["VTD"], inline=True)
        if data["AESTech"] != None:
            embed.add_field(name="AES Tech", value=data["AESTech"], inline=True)
        if data["SocketsSupported"] != None:
            embed.add_field(name="Sockets", value=data["SocketsSupported"], inline=True)
        if index:
            embed.set_footer(text=f"{index['current']+1} of {index['max']}")
        return embed

    async def get_search_results(self, search_term: str) -> Tuple[discord.Embed]:
        url: str = f"https://ark.intel.com/content/www/us/en/ark/search.html?_charset_=UTF-8&q={search_term}"
        search_page: soup = await make_soup(url)
        urls: Tuple[str] = self.get_urls(search_page)
        if not urls:
            return ()
        pages: List[soup] = []

        for url in urls:
            page: soup = await make_soup(url)
            pages.append(page)

        all_cpu_data: List[dict] = [self.get_cpu_data(i) for i in pages]
        embeds = [
            self.make_ark_embed(all_cpu_data[i], {"min": "0", "current": i, "max": len(all_cpu_data)})
            for i in range(len(all_cpu_data))
        ]
        return tuple(embeds)
