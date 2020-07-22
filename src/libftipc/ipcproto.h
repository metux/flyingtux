#ifndef __IPCPROTO_H
#define __IPCPROTO_H

#include <sys/socket.h>
#include <sys/un.h>

#define ERR_PTR(err)	((void*)(err))
#define PTR_ERR(ptr)	((long)(ptr))
#define IS_ERR(ptr)	((long)ptr < 1024)

struct ftux_mq {
    int refcnt;
    int fd;
    struct sockaddr_un addr;
    int (*handle)(struct ftux_mq *mq, int sz, void* data, int num_fd, int *fds);
    int (*close)(struct ftux_mq *mq);
    char* name;
};

struct ftux_mq* ftux_mq_get(const char* name);
int ftux_mq_put(struct ftux_mq *mq);
int ftux_mq_ref(struct ftux_mq *mq);

struct ftux_mq* ftux_mq_server(const char* name);
struct ftux_mq* ftux_mq_client(const char* name);

int ftux_mq_init(struct ftux_mq *mq, const char* name);

#endif
