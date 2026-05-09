import unittest

from scrapy.http import HtmlResponse, Request

from techpowerup.spiders.tpu import TpuSpider


class TpuSpiderMetricsTests(unittest.TestCase):
    def test_parse_gpu_records_response_and_item_metrics(self):
        spider = TpuSpider()
        request = Request(
            "https://www.techpowerup.com/gpu-specs/?year=2026",
            meta={"request_started_at": 100.0},
        )
        response = HtmlResponse(
            url=request.url,
            request=request,
            body=b"""
            <html>
              <body>
                <div id="list">
                  <table>
                    <tr class="vendor-nvidia">
                      <td><div class="item-name"><a>Example GPU</a></div></td>
                      <td>PCIe 5.0 x16</td>
                      <td>16 GB</td>
                      <td>2500 MHz</td>
                      <td>2000 MHz</td>
                      <td>128 / 64 / 32</td>
                      <td><div class="item-released">2026</div></td>
                      <td><div class="item-chip"><a>GB999</a></div></td>
                    </tr>
                  </table>
                </div>
              </body>
            </html>
            """,
            encoding="utf-8",
        )

        items = list(spider.parse(response))
        summary = spider.metrics.summary()

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["Product_Name"], "Example GPU")
        self.assertEqual(summary["response_count"], 1)
        self.assertEqual(summary["status_counts"], {200: 1})
        self.assertEqual(summary["parsed_items"], 1)
        self.assertEqual(summary["item_counts"], {"GPU": 1})


if __name__ == "__main__":
    unittest.main()
