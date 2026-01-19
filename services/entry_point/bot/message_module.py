import discord


def _generate_assets_links(assets: dict) -> str:
    assets = {k: v.replace("ipfs://", "https://ipfs.io/ipfs/") if v else v for k, v in assets.items()}
    assets_list = [
        f"[{key}]({value})" for key, value in assets.items() if value and key != "composite"
    ]

    # split by 3 per row
    assets_links = "\n".join(
        " · ".join(assets_list[i:i + 3])
        for i in range(0, len(assets_list), 3)
    )
    return assets_links


def get_notify_embed(data: dict) -> discord.Embed:
    # header
    title = data["title"]
    embed = discord.Embed(title=title, url="https://www.mash-it.io/mashers", color=discord.Color.green())

    # details
    artist_name = data["artistName"]
    listing = data.get("listing", {})

    price = listing["priceMatic"]
    max_supply = listing["maxSupply"]
    max_per_wallet = listing["maxPerWallet"]

    details = (
        f"""Artist: {artist_name}
Price: {price} USDC
Max Supply: {max_supply}
Max Per-Wallet: {max_per_wallet}"""
    )
    embed.add_field(name="Details", value=details, inline=False)

    # assets
    assets = data.get("assets", {})
    assets_links = _generate_assets_links(assets)
    embed.add_field(name="Assets:", value=assets_links, inline=False)

    # composite and footer
    composite_url = assets.get("composite").replace("ipfs://", "https://ipfs.io/ipfs/")
    embed.set_image(url=composite_url)
    embed.set_footer(text="Mashi")
    return embed
