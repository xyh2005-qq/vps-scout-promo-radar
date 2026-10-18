# ::ILANG
# ::STATE{@FILE, role:保留原始账期并计算明确标注的月均价格}
# ::BOUNDARY{never:把预付价格伪装成月付报价}
from decimal import Decimal

MONTHS={'month':1,'quarter':3,'year':12}
DURATIONS={'month':'P1M','quarter':'P3M','year':'P1Y'}
UPFRONT={'month':'Published monthly rate','quarter':'Full quarter upfront','year':'Full year upfront'}

def monthly_value(offer):
    return Decimal(offer['price'])/MONTHS[offer['billing']]
