import psycopg2
conn = psycopg2.connect('postgresql://toshiba:iopextoshiba2025@3.128.153.238:5432/toshiba_data')
cur = conn.cursor()

# Check FST technicians table structure
cur.execute('SELECT column_name FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position', ('fst_technicians',))
fst_columns = [row[0] for row in cur.fetchall()]
print('FST technicians columns:', fst_columns)

# Check a sample FST record
cur.execute('SELECT * FROM fst_technicians LIMIT 1')
sample_fst = cur.fetchone()
if sample_fst:
    column_names = [desc[0] for desc in cur.description]
    sample_dict = dict(zip(column_names, sample_fst))
    print('Sample FST record:', sample_dict)

# Check sample task assignee names
cur.execute('SELECT DISTINCT assignee_name FROM tasks WHERE assignee_name IS NOT NULL LIMIT 5')
task_names = [row[0] for row in cur.fetchall()]
print('Sample task assignee names:', task_names)

cur.close()
conn.close()