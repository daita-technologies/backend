import redis
conn = redis.Redis(host='localhost',port=6379,db=0)
print(conn.keys())
for key in conn.keys():
    conn.delete(key)
print("DELETE COMPLETED")