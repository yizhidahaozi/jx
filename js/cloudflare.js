const currentDomain = window.location.origin;
let isShowingIP = false;

async function getip() {
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
   const displayText = `访客:${info.loc} | ${info.http} | IP:${info.ip} | 节点:${info.colo} | 加密:${info.tls}`;
   return textContent = displayText;
  }
 } catch (error) {
  console.error("获取失败: ", error);
  return "显示失败";
 }
}

$(document).ready(function () {
 originalText = $("#cfs").text();

 $("#cfs").click(async function () {
  if (!isShowingIP) {
   const ip = await getip();
   $(this).text(`${ip}`);
  } else {
   $(this).text(originalText);
  }
  isShowingIP = !isShowingIP;
 });

 var t1 = performance.now();
 $("#time").text("页面加载耗时 " + Math.round(t1) + " 毫秒");

});
