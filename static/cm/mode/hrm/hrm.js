CodeMirror.defineSimpleMode('hrm', {
  // The start state contains the rules that are initially used
  start: [
    // Comment.
    {
      regex: /--.*$/,
      token: 'comment'
    },
    // Definition.
    {
      regex: /(DEFINE) (.*)$/i,
      token: ['keyword', 'comment'],
      next: 'comment'
    },
    // Command.
    {
      regex: /(inbox|outbox|copyfrom|copyto|add|sub|bumpup|bumpdn|jump|jumpz|jumpn)/i,
      token: ['builtin']
    },
    // Int
    {
      regex: /(\d+)/,
      token: ['number']
    },
    // Label definition.
    {
      regex: /([A-Z]+:)/i,
      token: ['string'],
      indent: true
    },
    // Label name.
    {
      regex: /([A-Z]+)/i,
      token: ['string'],
    },
  ],
  // The comment block.
  comment: [
    {regex: /;$/, token: 'comment', next: 'start'},
    {regex: /[^;]*/, token: 'comment'}
  ]
})
