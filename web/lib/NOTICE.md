# lib/ 외부 코드 표기

## peerjs.min.js
- PeerJS 1.5.5 — <https://peerjs.com> / <https://github.com/peers/peerjs>
- 라이선스 **MIT**
- 받은 곳: `https://unpkg.com/peerjs@1.5.5/dist/peerjs.min.js` (2026-08-19)
- 용도: 멀티플레이 전송(WebRTC P2P + 공용 시그널링). `web/net.js` 가 필요할 때만 읽는다.
- ★`//# sourceMappingURL` 한 줄을 지웠다. `.map` 을 같이 받지 않아서 콘솔에 404 가 남는다.
- ★스팀 빌드로 가면 이 파일 자리는 Steam Networking 어댑터가 대신한다(`net.js` 인터페이스는 그대로).
