import ePrint
from ePrint import ePrint_payload, ePrint_download

# 下载标题包含"gcm"，类别为"IMPLEMENTATION"且提交日期在2018年之后的论文至当前目录./
ePrint_download('./', ePrint_payload(title='gcm',
                                     category=ePrint.CATEGORY_IMPLEMENTATION,
                                     submittedafter='2018'))
