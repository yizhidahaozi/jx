const currentDomain = window.location.origin;

async function updateCloudflareInfo() {
 try {
  const response = await fetch("/cdn-cgi/trace");
  if (response.ok) {
   const data = await response.text();
   const lines = data.split("\n");
   const info = {};
   lines.forEach((line) => {
    const parts = line.split("=");
    if (parts.length === 2) {
     info[parts[0]] = parts[1];
    }
   });

   // 格式化显示信息
   const cfElement = document.getElementById("cfs");
   const displayText = ` | 访客:${info.loc} | ${info.http} | IP:${info.ip} | 节点:${info.colo} | 加密:${info.tls}`;
   cfElement.textContent = displayText;
  }
 } catch (error) {
  console.error("获取 Cloudflare 节点信息失败: ", error);
  document.getElementById("cfs").textContent = "获取节点信息失败";
 }
}

// 页面加载完成后获取信息
window.addEventListener("load", function () {
 // 页面加载时间计算
 var t1 = performance.now();
 document.getElementById("time").textContent = "页面加载耗时 " + Math.round(t1) + " 毫秒";

 // 获取 Cloudflare 信息
 updateCloudflareInfo();
});

// 每60秒更新一次信息
setInterval(updateCloudflareInfo, 60000);
