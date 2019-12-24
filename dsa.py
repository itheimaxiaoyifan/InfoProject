import time

t = time.localtime()
begin_mon_date_str = '%d-%02d-01' % (t.tm_year, t.tm_mon)
print(begin_mon_date_str)
print(t, type(t))
x = 1
print('%06d' % x)