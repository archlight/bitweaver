from Bridge import Bridge

files = {
    "object0001":
    {
        "type":     "com.symphony.hackathon.bitweaver",
        "version":  "1.0",
        "data":[]
    }
}

bridge = Bridge("bot.user21", "https://develop2.symphony.com", "https://develop2-api.symphony.com:8444","")
#bridge.renameRoom("RoDOROntj7QfyTZWQu1WoH___pxU3hyxdA", "New name for the chatRoom !", "Done by bot19")
#bridge.renameRoom("RoDOROntj7QfyTZWQu1WoH___pxU3hyxdA","12345678901234567890123456789012345678901234567890","room 2")

print(bridge.getUserStreamsInCsvFormat())


