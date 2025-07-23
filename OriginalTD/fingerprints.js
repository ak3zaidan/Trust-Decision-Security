const { getRandomFromList, getRandomNumberInRange } = require("./utils");

function getRandomFingerprint({ scriptHash, customTime, clientIdKey }) {
    let graphics = getRandomFromList([
        {
            unmasked:
                "Google Inc. (AMD)-&-ANGLE (AMD, AMD Radeon(TM) Graphics (0x00001638) Direct3D11 vs_5_0 ps_5_0, D3D11)",
            canvas: getRandomFromList(["8eaf90c1d72a767b1d6892772aefcfca"]),
        },
    ]);
    let webgl = getRandomFromList([
        "db68740ba90ba398363e70372c3d1795|0afadb3089bd6242ca7473c136424444",
    ]);
    let cpuCores = getRandomFromList([4, 8, 16]);
    let memory = getRandomFromList([4, 8]);
    let browser = getRandomFromList([
        {
            appVersion: "6a1b449d959f3bcc1b5df91403e9e6e5",
            userAgentData:
                "0_Windows_Not A(Brand_8_Chromium_132_Google Chrome_132",
            type: "Webkit-Chrome",
            appName: "Netscape",
            fonts: "263ce7fa479dc7c7c7b950b33c93d527|01100100011111111010111011011111011111011011110001111111111011111",
            userAgent:
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            appCodeName: "Mozilla",
        },
    ]);
    let screen = getRandomFromList([
        {
            clientHeight: 953,
            outerWidth: 1918,
            height: 1080,
            width: 1920,
            outerHeight: 1038,
            innerHeight: 953,
            clientWidth: 1920,
            availHeight: 1040,
        },
        {
            clientHeight: 735,
            outerWidth: 1539,
            height: 735,
            width: 1536,
            outerHeight: 735,
            innerHeight: 735,
            clientWidth: 1536,
            availHeight: 735,
        },
        {
            clientHeight: 738,
            outerWidth: 1536,
            height: 864,
            width: 1528,
            outerHeight: 816,
            innerHeight: 738,
            clientWidth: 1528,
            availHeight: 816,
        },
        {
            clientHeight: 738,
            outerWidth: 1536,
            height: 864,
            width: 1528,
            outerHeight: 816,
            innerHeight: 738,
            clientWidth: 1528,
            availHeight: 816,
        },
    ]);
    let a = [
        "en-US",
        browser.fonts,
        screen.outerWidth,
        "-",
        browser.userAgent,
        1,
        screen.innerHeight,
        "en-US",
        screen.clientWidth,
        screen.width,
        "-",
        browser.type,
        "functiongetParameter(){[nativecode]}",
        "132.0.6834.160",
        "-",
        "-",
        "10.0.0",
        getRandomNumberInRange(12545, 12551),
        "-",
        (customTime - 500).toString(32)
    ];
    let b = [
        "-",
        "Win32",
        screen.clientHeight,
        "0",
        "6ef4a53a32a3086171ad14d663a1e981",
        "-",
        330,
        cpuCores,
        "https%3A%2F%2Fwww.popmart.com%2Fth%2Fuser%2Flogin%3Fredirect%3D%252Faccount",
        browser.appVersion,
        customTime - 100,
        "1",
        "0",
        "[object Window]",
        "functiongetoffsetHeight(){[nativecode]}",
        "-",
        "Google Chrome",
        "UTF-8",
        "-",
        "-",
        (customTime - 400).toString(32)
    ];
    let c = [
        "-",
        screen.width,
        "67dddb1b61b76b0dfc179d9f32ea216c",
        "-",
        "291935",
        "11110",
        screen.availHeight,
        getRandomFromList([
            "48000_2_1_0_2_explicit_speakers",
            "44100_2_1_0_2_explicit_speakers",
        ]),
        screen.width,
        screen.outerHeight,
        "-",
        browser.appCodeName,
        screen.height,
        webgl,
        "1789594585__",
        graphics.canvas,
        "-",
        "-",
        getRandomNumberInRange(140, 250) +
            "_" +
            getRandomNumberInRange(28, 32) +
            "__0",
        "-",
        (customTime - 300).toString(32)
    ];
    let d = [
        "true_0_1_Infinity",
        0,
        browser.appName,
        0,
        "-",
        "-",
        "-",
        graphics.unmasked,
        "functioncreateAnalyser(){[nativecode]}",
        "-",
        "63337",
        "-",
        "1f2d82cb67327772481ce484582d66e4",
        browser.userAgentData,
        "-",
        "en-US|Asia/Calcutta",
        "-",//"152.58.30.193|",
        "-",//"0|36||1",
        (customTime - 200).toString(32)
    ];
    let g = [
        "1",
        cpuCores,
        "functiontoString(){[nativecode]}",
        "functiontoDataURL(){[nativecode]}",
        clientIdKey,
        "[objectPluginArray]",
        33,
        "-",
        memory,
        "functionRTCPeerConnection(){[nativecode]}",
        cpuCores,
        "functionenumerateDevices(){[nativecode]}",
        "-",
        memory,
        "-",
        "-",
        "-",
        "1696.5823364257812",
        "132.0.6834.160",
        "-",
        (customTime - 100).toString(32)
    ];

    let obj = {
        b: {
            a: a,
            b: b,
            c: c,
            d: d,
            e: "NHXmDzF1LnT1YyKoWHt5YvDbJkEmPwM43nfH8CSiynH8DxFvpju2MsSH3uTQDXmuGtfml76IjHWql4Sth0WltEoBxTeMwVOPvOrjWbgMXtE=",
            f: "1^^0^^0^^0^^0^^0",
            g: g,
        },
        bb: {},
        pageInfo: {},
        q: {
            appKey: "e8e328d27d9866dcf49ed2e0bb7411c4",
            partner: "popmart",
        },
        wb: "",
    };

    obj = {"bb":{"v":"4.0.4","os":3,"p":"popmart"},"pageInfo":{},"q":{"partner":"popmart","appKey":"e8e328d27d9866dcf49ed2e0bb7411c4"},"b":{"a":[customTime,"Win32",screen.innerHeight,screen.width,browser.appVersion,0,330,"https%3A%2F%2Fwww.popmart.com%2Fus",screen.width,"en-US","1",screen.width,1,"true_0_1_Infinity","-","functiongetParameter(){[nativecode]}","132.0.6834.160","Google Chrome","-","1f2d82cb67327772481ce484582d66e4","-","1ijjpt121"],"b":["en-US","-","-",browser.fonts,screen.height,screen.innerHeight,"-","-",graphics.unmasked,"[object Window]","-","-","-",browser.userAgentData,"-","en-US|Asia/Calcutta","0|38||1","1ijjpt137"],"c":["-","6ef4a53a32a3086171ad14d663a1e981",0,"0","Netscape","11110","563185","-",screen.innerHeight,16,"44100_2_1_0_2_explicit_speakers","0","-","662","132.0.6834.160","-","10.0.0",12545,"-","1ijjpt142"],"d":["-",screen.width,browser.userAgent,graphics.canvas,"-",screen.availHeight,"-",screen.width,"Mozilla",webgl,"Webkit-Chrome","functiongetoffsetHeight(){[nativecode]}","f3403a0c9cd914f77ac6810ac04d196a","UTF-8","-","-","-","152.59.8.4|","1ijjpt14h"],"g":["-",clientIdKey,"functiontoDataURL(){[nativecode]}","functionRTCPeerConnection(){[nativecode]}","1",16,8,"functiontoString(){[nativecode]}",8,33,"functionenumerateDevices(){[nativecode]}",16,"1","[objectPluginArray]","functioncreateAnalyser(){[nativecode]}","-","1696.5823364257812","2231966371__","-","-","-","171_30__0","1ijjpt15u"],"f":"1^^0^^0^^0^^0^^0","e":"asdasd"},"wb":""}
    return { fp: obj, ua: browser.userAgent, gpu: graphics.unmasked };
}

module.exports = { getRandomFingerprint };
