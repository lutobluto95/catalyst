from sqlparse import format
import psycopg2
import pandas

def generateSQL(kpi_name, group_ids, tx, date_range):
    if kpi_name not in ['mentions','conv']: raise ValueError("kpi name can only have 'mentions' and 'conv' as values")
    group_ids = tuple(group_ids)
    queries = {
        'mentions':f"""Select groupid, createdatutc,textlower, sentimentrvalue,sourceid,parentsourceid,type from bd_cs_prod_conversations
                    where groupid in {group_ids} and ({tx}) and ({date_range})""",

        'conv':f"""Select groupid,createdatutc,textlower,sentimentrvalue,sourceid,parentsourceid,type
                        from 
                        bd_cs_prod_conversations 
                        where 
                        groupid in {group_ids} and ({tx}) and ({date_range})

                        union

                        Select groupid,createdatutc,textlower,sentimentrvalue,sourceid,parentsourceid,type
                        from bd_cs_prod_conversations 
                        where parentsourceid IN (
                        Select sourceid
                        from 
                        bd_cs_prod_conversations 
                        where 
                        groupid in {group_ids}
                        and
                        (
                        {tx}
                        ) 
                        and (type = 'Post') 
                        and (grouptype = 'Facebook') 
                        and 
                        ( {date_range}
                        )
                        )
                        and (type = 'Comment') and ({date_range})""",
    }
    return format(queries[kpi_name], reindent=True, keyword_case='upper')

def makeConnection(dbname, host, port, user, password):
    return psycopg2.connect(
        dbname=dbname, 
        host=host, 
        port=port,
        user=user, 
        password=password)

def executeQuery(connection, query):
    with connection.cursor() as cur1:
        cur1.execute(query)
        output = cur1.fetchall()
    try: 
        output_df = pandas.DataFrame(output)
        output_df.columns = ['groupid','createdatutc','textlower','senti','sourceid','parentsourceid','type']
        backup = output_df.copy()
    except ValueError as e:
        
        output_df = pandas.DataFrame(columns=['groupid','createdatutc','textlower','senti','sourceid','parentsourceid','type'])
    return output_df