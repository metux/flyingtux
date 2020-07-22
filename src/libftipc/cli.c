#include <sys/socket.h>
#include <sys/un.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "ipcproto.h"

char *socket_path = "./socket";

int main(int argc, char *argv[]) {
    char buf[100];
    int rc;
    struct ftux_mq *mq;

    if (argc > 1) socket_path=argv[1];

    mq = ftux_mq_get(socket_path);

    if (connect(mq->fd, (struct sockaddr*)&(mq->addr), sizeof(mq->addr)) == -1) {
        perror("connect error");
        exit(-1);
    }

    while( (rc=read(STDIN_FILENO, buf, sizeof(buf))) > 0) {
        if (write(mq->fd, buf, rc) != rc) {
            if (rc > 0) fprintf(stderr,"partial write");
            else {
                perror("write error");
                exit(-1);
            }
        }
    }

    return 0;
}
