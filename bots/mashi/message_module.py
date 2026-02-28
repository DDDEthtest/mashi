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


def get_notify_embed(data: dict, is_release: bool) -> discord.Embed:
    # header
    title = data["title"]
    # details
    artist_name = data["artistName"]

    url = "https://mash-it.io/mashers"

    if is_release:
        listing = data.get("listing", {})

        listing_id = listing.get("listingId")
        price = listing["priceMatic"]
        max_supply = listing["maxSupply"]
        max_per_wallet = listing["maxPerWallet"]
        url = f"https://mash-it.io/mashers?listing={listing_id}"

    embed = discord.Embed(title=title, url=url, color=discord.Color.green())

    if is_release:
        details = (
            f"""Artist: {artist_name}
Price: {price} USDC
Max Supply: {max_supply}
Max Per-Wallet: {max_per_wallet}"""
        )
    else:
        details = f"Artist: {artist_name}"

    embed.add_field(name="Details", value=details, inline=False)

    # assets
    assets = data.get("assets", {})
    assets_links = _generate_assets_links(assets)
    embed.add_field(name="Assets:", value=assets_links, inline=False)

    # composite and footer
    composite_url = assets.get("composite").replace("ipfs://", "https://ipfs.io/ipfs/")
    embed.set_image(url=composite_url)
    embed.set_footer(text=f"© 2026 mash-it x {artist_name}")
    return embed
