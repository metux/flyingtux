# SPDX-License-Identifier: AGPL-3.0-or-later
#FROM debian
#RUN apt-get update && apt-get upgrade -y
#RUN apt-get install -y squid

FROM sameersbn/squid:3.5.27-2
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y mc

COPY squid.conf /etc/squid
