// macOS Vision 글자 인식. 사용: swift img_ocr.swift [--lang ko|ja] <png ...>  → JSON(stdout)
// 결과: [{file, W, H, items:[{t, conf, box:[x,y,w,h], chars:[[x,y,w,h]...]}]}]
import Foundation
import Vision
import AppKit

var args = Array(CommandLine.arguments.dropFirst())
var langs = ["ko-KR", "en-US"]
if args.first == "--lang" {
  let l = args[1]; args.removeFirst(2)
  langs = l == "ja" ? ["ja-JP", "en-US"] : ["ko-KR", "en-US"]
}
var out: [[String: Any]] = []
for path in args {
  guard let img = NSImage(contentsOfFile: path), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { continue }
  let W = Double(cg.width), H = Double(cg.height)
  let req = VNRecognizeTextRequest()
  req.recognitionLevel = .accurate
  req.recognitionLanguages = langs
  req.usesLanguageCorrection = false
  req.minimumTextHeight = 0.004
  try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([req])
  var items: [[String: Any]] = []
  for o in req.results ?? [] {
    guard let c = o.topCandidates(1).first else { continue }
    let s = c.string; let b = o.boundingBox
    var chars: [[Double]] = []
    var i = s.startIndex
    while i < s.endIndex {
      let j = s.index(after: i)
      if let bb = try? c.boundingBox(for: i..<j)?.boundingBox {
        chars.append([bb.minX*W, (1-bb.maxY)*H, bb.width*W, bb.height*H])
      } else { chars.append([-1,-1,-1,-1]) }
      i = j
    }
    items.append(["t": s, "conf": c.confidence, "box": [b.minX*W, (1-b.maxY)*H, b.width*W, b.height*H], "chars": chars])
  }
  out.append(["file": (path as NSString).lastPathComponent, "W": W, "H": H, "items": items])
}
print(String(data: try! JSONSerialization.data(withJSONObject: out), encoding: .utf8)!)
