#coding=utf-8

from basic import BasicCtrl

class PostsCtrl(BasicCtrl):
    def get(self, _tnm = None):
        pager = {}
        pager['qnty'] = 5
        pager['page'] = max(int(self.input('page', 1)), 1)
        pager['list'] = 0;

        stime = self.stime()
        track = ''

        cur = self.dbase('posts').cursor()

        _qry = self.input('q', None)
        _top = False
        _tag = None

        if _tnm:
            cur.execute('select * from terms where term_sign = ? limit 1', (str(_tnm).lower(),))
            _tag = cur.fetchone()

        if _tag:
            cur.execute('select posts.* from posts,post_terms where posts.post_id=post_terms.post_id and term_id=? and post_stat>0 and post_ptms<? order by post_ptms desc limit ? offset ?', (_tag['term_id'], stime, pager['qnty'], (pager['page']-1)*pager['qnty'], ))
            posts = cur.fetchall()
            track = '标签：' + _tag['term_name']
        elif _tnm:
            self.send_error(404)
            return
        elif _qry:
            cur.execute('select * from posts where post_stat>0 and post_ptms<? and (post_title like ? or post_content like ?) order by post_ptms desc limit ? offset ?', (stime, '%'+_qry+'%', '%'+_qry+'%', pager['qnty'], (pager['page']-1)*pager['qnty'], ))
            posts = cur.fetchall()
            track = '搜索：' + _qry
        else:
            cur.execute('select * from posts where post_stat>0 and post_ptms<? order by post_ptms desc limit ? offset ?', (stime, pager['qnty'], (pager['page']-1)*pager['qnty'], ))
            posts = cur.fetchall()

            if self.input('page', None) is None:
                _top = True

        ptids = {}
        ptags = {}
        if posts:
            pager['list'] = len(posts)

            cur.execute('select post_id,term_id from post_terms where post_id in (' + ','.join(str(i['post_id']) for i in posts) + ')')
            ptids = cur.fetchall()
            if ptids:
                cur.execute('select * from terms where term_id in (' + ','.join(str(i['term_id']) for i in ptids) + ')')
                ptags = cur.fetchall()
                if ptags:
                    ptids = self.utils().array_group(ptids, 'post_id')
                    ptags = self.utils().array_keyto(ptags, 'term_id')

        cur.execute('select * from terms where term_refc>0 order by term_refc desc, term_id desc limit 32')
        keyws_tag = cur.fetchall()

        cur.execute('select post_id,post_title,post_ptms from posts where post_stat>0 and post_ptms<? order by post_rank desc, post_id desc limit 9', (stime,))
        posts_top = cur.fetchall()

        cur.execute('select post_id,post_title,post_ptms from posts where post_stat>0 and post_ptms<? order by post_remc desc, post_id desc limit 9', (stime,))
        posts_hot = cur.fetchall()

        cur.execute('select post_id,post_title,post_ptms from posts where post_stat>0 and post_ptms<? order by post_ptms desc, post_id desc limit 9', (stime,))
        posts_new = cur.fetchall()

        cur.close()

        cur = self.dbase('talks').cursor()
        cur.execute('select * from talks where talk_rank>0 order by talk_id desc limit 9')
        talks_new = cur.fetchall()
        cur.close()

        if _top:
            cur = self.dbase('links').cursor()
            cur.execute('select * from links where link_rank>=? order by link_rank desc, link_id desc limit 99', (self.get_runtime_conf('index_links_min_rank'), ))
            links_top = cur.fetchall()
            cur.close()
        else:
            links_top = None

        self.render('posts.html', track = track, pager = pager, posts = posts, ptids = ptids, ptags = ptags\
                , posts_top = posts_top, posts_hot = posts_hot, posts_new = posts_new, keyws_tag = keyws_tag, talks_new = talks_new, links_top = links_top)


class PostCtrl(BasicCtrl):
    def get(self, post_id):
        stime = self.stime()

        cur = self.dbase('posts').cursor()
        cur.execute('select * from posts where post_id = ?', (post_id, ))
        post = cur.fetchone()

        if not post or ((not self.get_current_user()) and (not post['post_stat'] or post['post_ptms'] >= stime)):
            cur.close()
            return self.send_error(404)

        ptids = {}
        ptags = {}
        if post:
            cur.execute('select post_id,term_id from post_terms where post_id = ?', (post_id, ))
            ptids = cur.fetchall()
            if ptids:
                cur.execute('select * from terms where term_id in (' + ','.join(str(i['term_id']) for i in ptids) + ')')
                ptags = cur.fetchall()
                if ptags:
                    ptids = self.utils().array_group(ptids, 'post_id')
                    ptags = self.utils().array_keyto(ptags, 'term_id')

        cur.execute('select post_id from posts where post_stat>0 and post_ptms<? and post_id<? order by post_id desc limit 1', (stime, post_id, ))
        post_prev = cur.fetchone()
        if post_prev:
            post_prev = post_prev['post_id']
        else:
            post_prev = 0

        cur.execute('select post_id from posts where post_stat>0 and post_ptms<? and post_id>? order by post_id asc limit 1', (stime, post_id, ))
        post_next = cur.fetchone()
        if post_next:
            post_next = post_next['post_id']
        else:
            post_next = 0

        cur.execute('select * from terms where term_refc>0 order by term_refc desc, term_id desc limit 32')
        keyws_tag = cur.fetchall()

        cur.execute('select post_id,post_title,post_ptms from posts where post_stat>0 and post_ptms<? order by post_rank desc, post_id desc limit 9', (stime,))
        posts_top = cur.fetchall()

        cur.execute('select post_id,post_title,post_ptms from posts where post_stat>0 and post_ptms<? order by post_remc desc, post_id desc limit 9', (stime,))
        posts_hot = cur.fetchall()

        cur.execute('select post_id,post_title,post_ptms from posts where post_stat>0 and post_ptms<? order by post_ptms desc, post_id desc limit 9', (stime,))
        posts_new = cur.fetchall()

        cur.close()
        cur = self.dbase('talks').cursor()

        cur.execute('select * from talks where talk_rank>0 order by talk_id desc limit 9')
        talks_new = cur.fetchall()

        cur.execute('select * from talks where post_id = ? and talk_rank > 0 order by talk_id asc', (post['post_id'],))
        talks = cur.fetchall()
        cur.close()

        links_top = None

        self.render('post.html', post = post, ptids = ptids, ptags = ptags, talks = talks\
                , post_prev = post_prev, post_next = post_next\
                , posts_top = posts_top, posts_hot = posts_hot, posts_new = posts_new, keyws_tag = keyws_tag, talks_new = talks_new, links_top = links_top)
