FROM binwiederhier/ntfy:latest
EXPOSE 80
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["ntfy serve --listen-http \":${PORT:-80}\""]
