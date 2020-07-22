#include <stdio.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <stdlib.h>
#include <string.h>

#include "ipcproto.h"

char *socket_path = "./socket";

int main(int argc, char *argv[]) {
    char buf[100];
    int cl,rc;
    struct ftux_mq *mq;

    if (argc > 1) socket_path=argv[1];

//    mq = ftux_mq_get(socket_path);
    mq = ftux_mq_server(socket_path);

    if (IS_ERR(mq)) {
        fprintf(stderr, "sock error: %s\n", strerror(PTR_ERR(mq)));
        exit(-1);
    }

//    unlink(socket_path);
//    if (bind(mq->fd, (struct sockaddr*)&(mq->addr), sizeof(mq->addr)) == -1) {
//        perror("bind error");
//        exit(-1);
//    }

//    if (listen(mq->fd, 5) == -1) {
//        perror("listen error");
//        exit(-1);
//    }

    while (1) {
        if ( (cl = accept(mq->fd, NULL, NULL)) == -1) {
            perror("accept error");
            continue;
        }

        while ( (rc=read(cl,buf,sizeof(buf))) > 0) {
            printf("read %u bytes: %.*s\n", rc, rc, buf);
        }
        if (rc == -1) {
            perror("read");
            exit(-1);
        }
        else if (rc == 0) {
            printf("EOF\n");
            close(cl);
        }
    }

    return 0;
}
