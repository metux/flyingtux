
#include <stdio.h>

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <netdb.h>
#include <netinet/in.h>
#include <string.h>
#include <errno.h>

#include "ipcproto.h"

struct ftux_mq* ftux_mq_get(const char* name)
{
    int err;
    struct ftux_mq *mq = malloc(sizeof(struct ftux_mq));

    if (IS_ERR(mq)) {
        perror("whhops. malloc returned an unusable address\n");
    }

    memset(mq, 0, sizeof(struct ftux_mq));
    mq->name = strdup(name);
    mq->refcnt = 1;
    mq->addr.sun_family = AF_UNIX;
    strncpy(mq->addr.sun_path, name, sizeof(mq->addr.sun_path)-1);

    if ( (err = mq->fd = socket(AF_UNIX, SOCK_STREAM, 0)) == -1)
        goto err;

    return mq;

err:
    free(mq);
    fprintf(stderr, "ftux_mq_get() error: %s\n", strerror(-err));
    return ERR_PTR(-err);
}

int ftux_mq_put(struct ftux_mq *mq)
{
    if (IS_ERR(mq))
        return -EINVAL;

    mq->refcnt--;
    if (mq->refcnt > 0)
        return 0;

    if (mq->name)
        free(mq->name);

    free(mq);
    return 0;
}

struct ftux_mq* ftux_mq_server(const char* name)
{
    struct ftux_mq *mq;
    int err;

    mq = ftux_mq_get(name);
    if (IS_ERR(mq)) {
        fprintf(stderr, "failed to get mq: %s\n", strerror(PTR_ERR(mq)));
        return mq;
    }

    unlink(name);

    if (bind(mq->fd, (struct sockaddr*)&(mq->addr), sizeof(mq->addr)) == -1) {
        perror("bind error");
        goto err;
    }

    if (listen(mq->fd, 5) == -1) {
        perror("listen error");
        goto err;
    }

    return mq;

err:
    err = errno;
    ftux_mq_put(mq);
    return ERR_PTR(err);
}
