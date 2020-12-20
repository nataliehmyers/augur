#SPDX-License-Identifier: MIT
import base64
import sqlalchemy as s
import pandas as pd
import json
from flask import Response
import datetime
import traceback

def create_routes(server):
    
    def try_func(func):
        def f(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                traceback.print_exc()
                raise e
        return f
    
    @try_func
    def helper_get_issues_with_timestamp_field_between(repo_id, field: str, begin: datetime.datetime, end: datetime.datetime) -> int:
        begin_str = begin.strftime('%Y-%m-%d %H:%M:%S')
        end_str = end.strftime('%Y-%m-%d %H:%M:%S')
        
        issueCountSQL = s.sql.text(f"""
            SELECT
                repo.repo_id,
                COUNT(issue_id) as issue_count
            FROM repo JOIN issues ON repo.repo_id = issues.repo_id
            WHERE repo.repo_id = :repo_id
            AND issues.{field} BETWEEN to_timestamp(:begin_str, 'YYYY-MM-DD HH24:MI:SS') AND to_timestamp(:end_str, 'YYYY-MM-DD HH24:MI:SS')
            GROUP BY repo.repo_id
        """)
        results = pd.read_sql(issueCountSQL, server.augur_app.database, params={
            'repo_id': repo_id,
            'begin_str': begin_str,
            'end_str': end_str
        })
        
        if len(results) < 1:
            return 0
        else:
            return results[0]['issue_count']
    
    @try_func
    def helper_get_open_issues_with_timestamp_field_between(repo_id, field: str, begin: datetime.datetime, end: datetime.datetime) -> int:
        begin_str = begin.strftime('%Y-%m-%d %H:%M:%S')
        end_str = end.strftime('%Y-%m-%d %H:%M:%S')
        
        issueCountSQL = s.sql.text(f"""
            SELECT
                repo.repo_id,
                COUNT(issue_id) as issue_count
            FROM repo JOIN issues ON repo.repo_id = issues.repo_id
            WHERE repo.repo_id = :repo_id
            WHERE issues.closed_at IS NULL
            AND issues.{field} BETWEEN to_timestamp(:begin_str, 'YYYY-MM-DD HH24:MI:SS') AND to_timestamp(:end_str, 'YYYY-MM-DD HH24:MI:SS')
            GROUP BY repo.repo_id
        """)
        results = pd.read_sql(issueCountSQL, server.augur_app.database, params={
            'repo_id': repo_id,
            'begin_str': begin_str,
            'end_str': end_str
        })
        
        if len(results) < 1:
            return 0
        else:
            return results[0]['issue_count']
        

    @server.app.route('/{}/giants-project/repos'.format(server.api_version))
    def get_all_repo_ids_name_names():
        reposSQL = s.sql.text("""
            SELECT repo.repo_id, repo.repo_name
            FROM repo
            ORDER BY repo.repo_name
        """)
        results = pd.read_sql(reposSQL, server.augur_app.database)
        data_str = results.to_json(orient="records", date_format='iso', date_unit='ms')
        #data = json.loads(data_str)
        #list_data = [item['repo_id'] for item in data]
        #list_data_str = json.dumps(list_data)
        return Response(response=data_str,
                        status=200,
                        mimetype="application/json")

    @server.app.route('/{}/giants-project/status/<repo_id>'.format(server.api_version))
    @try_func
    def get_repo_status(repo_id):
        reposSQL = s.sql.text("""
            SELECT repo.repo_id, repo.repo_name
            FROM repo
            WHERE repo.repo_id = :repo_id
        """)
        results = pd.read_sql(reposSQL, server.augur_app.database, params={'repo_id': repo_id})
        data_str = results.to_json(orient="records", date_format='iso', date_unit='ms')
		# TODO: also add basic metric information like listed on https://github.com/zachs18/augur/issues/6
        data = json.loads(data_str)
        
        now = datetime.datetime.now()
        week = datetime.timedelta(days=7)
        year = datetime.timedelta(days=365)
        
        issues_created_past_week = helper_get_issues_with_timestamp_field_between(repo_id, "created_at", now - week, now)
        issues_created_past_year = helper_get_issues_with_timestamp_field_between(repo_id, "created_at", now - year, now)
        
        issues_closed_past_week = helper_get_issues_with_timestamp_field_between(repo_id, "closed_at", now - week, now)
        issues_closed_past_year = helper_get_issues_with_timestamp_field_between(repo_id, "closed_at", now - year, now)
        
        data[0]['issues_created_past_week'] = issues_created_past_week
        data[0]['issues_created_past_year'] = issues_created_past_year
        data[0]['issues_closed_past_week'] = issues_closed_past_week
        data[0]['issues_closed_past_year'] = issues_closed_past_year
        
        return Response(response=json.dumps(data),
                        status=200,
                        mimetype="application/json")

    @server.app.route('/{}/giants-project/test1/<repo_id>'.format(server.api_version))
    def get_repo_test1(repo_id):
        try:
            this_week_begin = datetime.datetime.now() - datetime.timedelta(days=7)
            this_week_end = datetime.datetime.now()
            
            begin_date = this_week_begin.strftime('%Y-%m-%d %H:%M:%S')
            end_date = this_week_end.strftime('%Y-%m-%d %H:%M:%S')
            
            issueCountSQL = s.sql.text("""
                SELECT
                    repo.repo_id,
                    COUNT(issue_id) as issue_count
                FROM repo JOIN issues ON repo.repo_id = issues.repo_id
                WHERE repo.repo_id = :repo_id
                AND issues.created_at BETWEEN to_timestamp(:begin_date, 'YYYY-MM-DD HH24:MI:SS') AND to_timestamp(:end_date, 'YYYY-MM-DD HH24:MI:SS')
                GROUP BY repo.repo_id
            """)
            results = pd.read_sql(issueCountSQL, server.augur_app.database, params={
                'repo_id': repo_id,
                'begin_date': begin_date,
                'end_date': end_date
            })
            data_str = results.to_json(orient="records", date_format='iso', date_unit='ms')
            # TODO: also add basic metric information like listed on https://github.com/zachs18/augur/issues/6
            data = json.loads(data_str)

            return Response(response=data_str,
                            status=200,
                            mimetype="application/json")
        except Exception as e:
            print(e)
'''
    @server.app.route('/{}/repos'.format(server.api_version))
    def get_all_repos():

        get_all_repos_sql = s.sql.text("""
            SELECT
                repo.repo_id,
                repo.repo_name,
                repo.description,
                repo.repo_git AS url,
                repo.repo_status,
                a.commits_all_time,
                b.issues_all_time ,
                rg_name,
                repo.repo_group_id
            FROM
                repo
                left outer join
                (select repo_id,    COUNT ( distinct commits.cmt_commit_hash ) AS commits_all_time from commits group by repo_id ) a on
                repo.repo_id = a.repo_id
                left outer join
                (select repo_id, count ( * ) as issues_all_time from issues where issues.pull_request IS NULL  group by repo_id) b
                on
                repo.repo_id = b.repo_id
                JOIN repo_groups ON repo_groups.repo_group_id = repo.repo_group_id
            order by repo_name
        """)
        results = pd.read_sql(get_all_repos_sql, server.augur_app.database)
        results['url'] = results['url'].apply(lambda datum: datum.split('//')[1])

        b64_urls = []
        for i in results.index:
            b64_urls.append(base64.b64encode((results.at[i, 'url']).encode()))
        results['base64_url'] = b64_urls

        data = results.to_json(orient="records", date_format='iso', date_unit='ms')
        return Response(response=data,
                        status=200,
                        mimetype="application/json")

    @server.app.route('/{}/repo-groups/<repo_group_id>/repos'.format(server.api_version))
    def get_repos_in_repo_group(repo_group_id):
        repos_in_repo_groups_SQL = s.sql.text("""
            SELECT
                repo.repo_id,
                repo.repo_name,
                repo.description,
                repo.repo_git AS url,
                repo.repo_status,
                a.commits_all_time,
                b.issues_all_time
            FROM
                repo
                left outer join
                (select repo_id, COUNT ( distinct commits.cmt_commit_hash ) AS commits_all_time from commits group by repo_id ) a on
                repo.repo_id = a.repo_id
                left outer join
                (select repo_id, count ( issues.issue_id) as issues_all_time from issues where issues.pull_request IS NULL group by repo_id) b
                on
                repo.repo_id = b.repo_id
                JOIN repo_groups ON repo_groups.repo_group_id = repo.repo_group_id
            WHERE
                repo_groups.repo_group_id = :repo_group_id
            ORDER BY repo.repo_git
        """)

        results = pd.read_sql(repos_in_repo_groups_SQL, server.augur_app.database, params={'repo_group_id': repo_group_id})
        data = results.to_json(orient="records", date_format='iso', date_unit='ms')
        return Response(response=data,
                        status=200,
                        mimetype="application/json")

    @server.app.route('/{}/owner/<owner>/name/<repo>'.format(server.api_version))
    def get_repo_by_git_name(owner, repo):

        get_repo_by_git_name_sql = s.sql.text("""
            SELECT repo.repo_id, repo.repo_group_id, rg_name
            FROM repo JOIN repo_groups ON repo_groups.repo_group_id = repo.repo_group_id
            WHERE repo_name = :repo AND repo_path LIKE :owner
            GROUP BY repo_id, rg_name
        """)

        results = pd.read_sql(get_repo_by_git_name_sql, server.augur_app.database, params={'owner': '%{}_'.format(owner), 'repo': repo,})
        data = results.to_json(orient="records", date_format='iso', date_unit='ms')
        return Response(response=data,
                        status=200,
                        mimetype="application/json")

    @server.app.route('/{}/rg-name/<rg_name>/repo-name/<repo_name>'.format(server.api_version))
    def get_repo_by_name(rg_name, repo_name):

        get_repo_by_name_sql = s.sql.text("""
            SELECT repo_id, repo.repo_group_id, repo_git as url
            FROM repo, repo_groups
            WHERE repo.repo_group_id = repo_groups.repo_group_id
            AND LOWER(rg_name) = LOWER(:rg_name)
            AND LOWER(repo_name) = LOWER(:repo_name)
        """)
        results = pd.read_sql(get_repo_by_name_sql, server.augur_app.database, params={'rg_name': rg_name, 'repo_name': repo_name})
        results['url'] = results['url'].apply(lambda datum: datum.split('//')[1])
        data = results.to_json(orient="records", date_format='iso', date_unit='ms')
        return Response(response=data,
                        status=200,
                        mimetype="application/json")

    @server.app.route('/{}/rg-name/<rg_name>'.format(server.api_version))
    def get_group_by_name(rg_name):
        groupSQL = s.sql.text("""
            SELECT repo_group_id, rg_name
            FROM repo_groups
            WHERE lower(rg_name) = lower(:rg_name)
        """)
        results = pd.read_sql(groupSQL, server.augur_app.database, params={'rg_name': rg_name})
        data = results.to_json(orient="records", date_format='iso', date_unit='ms')
        return Response(response=data,
                        status=200,
                        mimetype="application/json")

    @server.app.route('/{}/dosocs/repos'.format(server.api_version))
    def get_repos_for_dosocs():
        get_repos_for_dosocs_SQL = s.sql.text("""
            SELECT b.repo_id, CONCAT(a.value || b.repo_group_id || chr(47) || b.repo_path || b.repo_name) AS path
            FROM settings a, repo b
            WHERE a.setting='repo_directory'
        """)

        results = pd.read_sql(get_repos_for_dosocs_SQL, server.augur_app.database)
        data = results.to_json(orient="records", date_format='iso', date_unit='ms')
        return Response(response=data,
                        status=200,
                        mimetype='application/json')

    @server.app.route('/{}/repo-groups/<repo_group_id>/get-issues'.format(server.api_version))
    @server.app.route('/{}/repos/<repo_id>/get-issues'.format(server.api_version))
    def get_issues(repo_group_id, repo_id=None):
        if not repo_id:
            get_issues_sql = s.sql.text("""
                SELECT issue_title,
                    issues.issue_id,
                    issues.repo_id,
                    issues.html_url,
                    issue_state                                 AS STATUS,
                    issues.created_at                           AS DATE,
                    count(issue_events.event_id),
                    MAX(issue_events.created_at)                AS LAST_EVENT_DATE,
                    EXTRACT(DAY FROM NOW() - issues.created_at) AS OPEN_DAY
                FROM issues,
                    issue_events
                WHERE issues.repo_id IN (SELECT repo_id FROM repo WHERE repo_group_id = :repo_group_id)
                AND issues.issue_id = issue_events.issue_id
                AND issues.pull_request is NULL
                GROUP BY issues.issue_id
                ORDER by OPEN_DAY DESC
            """)
            results = pd.read_sql(get_issues_sql, server.augur_app.database, params={'repo_group_id': repo_group_id})
        else:
            get_issues_sql = s.sql.text("""
                SELECT issue_title,
                    issues.issue_id,
                    issues.repo_id,
                    issues.html_url,
                    issue_state                                 AS STATUS,
                    issues.created_at                           AS DATE,
                    count(issue_events.event_id),
                    MAX(issue_events.created_at)                AS LAST_EVENT_DATE,
                    EXTRACT(DAY FROM NOW() - issues.created_at) AS OPEN_DAY,
                    repo_name
                FROM issues JOIN repo ON issues.repo_id = repo.repo_id, issue_events
                WHERE issues.repo_id = :repo_id
                AND issues.pull_request IS NULL 
                AND issues.issue_id = issue_events.issue_id
                GROUP BY issues.issue_id, repo_name
                ORDER by OPEN_DAY DESC
            """)
            results = pd.read_sql(get_issues_sql, server.augur_app.database, params={'repo_id': repo_id})
        data = results.to_json(orient="records", date_format='iso', date_unit='ms')
        return Response(response=data,
                        status=200,
                        mimetype='application/json')

    @server.app.route('/{}/api-port'.format(server.api_version))
    def api_port():
        response = {'port': server.augur_app.config.get_value('Server', 'port')}
        return Response(response=json.dumps(response),
                        status=200,
                        mimetype="application/json")
'''
