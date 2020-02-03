# Scrapy 知网专利[基础信息]爬虫
>## 思路
>detail.py爬虫的爬取格式如下：
>```
>[
>   {
>       'dbcode': 'scpd',
>       'dbname': 'scpd年份',
>        'filename': 专利公开号
>   }
>   ,
>   //...
>]
>```
>该爬虫目前会便利files/pending/下的所有文件，并yield Request
>## spider
>detail 爬虫：负责爬取详情页
>## middleware
>1. GetFromLocalityMiddleware 用于从本地获取文件，如果获取成功，则直接从本地获取
>2. RetryOrErrorMiddleware 重写官方代码，添加一个报错日志
>3. ProxyMiddleware 添加代理 在这个函数中会由requests请求获得代理
>## pipeline
>1. SavePagePipeline 保存到本地文件
>2. FilterPipeline 把得到的item的格式改为正确的格式
>3. MongoPipeline 保存到mongo数据库中
>4. JsonPipeline 存储到json文件中
>## 关于思路
>### 1.代理     
> 每个请求都会重试若干次以上（代理不可用），同时会在最后一次不再使用代理
>如果最后一次仍然失败，则将该出错记录下来。
>### 2.数据清洗
>数据可以保存到JSON/MongoDB中，同时，注意保证公开号的唯一
>目前有两个数据类型为数组：发明人和专利分类号(源数据用分号隔开)
>注：发明人 专利分类号 中间用分号隔开 就算只有一个也是用数组

>
>要有两个线程，线程之间相互合作，生产者就是run.py 消费者则是scrapy，它们共同管理
>着一个队列，run.py负责读取文件，并把数据放入队列中；而scrapy则负责从队列中提取数据
>
>category_code 根据文件夹可以得知
>是放在服务器上跑，还是跑完了一大类后再进行。。。
>有的专利页面没有专利代理机构和代理人
>### 数据提取
>可以按照tr[style!='display:none']提取每一行，接着xpath('./td').extract()提取出
>该行所有的td
>```
>for td in tds:
>   if td.text() in self.mapping():
>       key = self.mappings()
>       value = td.next()
>       item[key] = value
>```
