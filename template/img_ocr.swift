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
// 가로로 아주 긴 이미지(표 한 줄 조각, 폭이 높이의 2.5배 넘고 1200px 넘음)는 Vision이 글자를 거의 못 읽는다(2026-11-03 Query 3.1 둘째 캡처 3130×196px에서 2개만 읽음).
// 그래서 폭을 높이의 3배(최소 1200px) 조각으로 잘라 200px씩 겹치게 읽고, 조각 자른 가장자리에 걸린 글자는 버린 뒤 합친다.
func recognize(_ cg: CGImage) -> [[String: Any]] {
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
  return items
}
func shifted(_ it: [String: Any], _ dx: Double) -> [String: Any] {
  var r = it
  let b = it["box"] as! [Double]; r["box"] = [b[0] + dx, b[1], b[2], b[3]]
  r["chars"] = (it["chars"] as! [[Double]]).map { $0[0] < 0 ? $0 : [$0[0] + dx, $0[1], $0[2], $0[3]] }
  return r
}
func overlapRatio(_ a: [Double], _ b: [Double]) -> Double {
  let ix = max(0, min(a[0]+a[2], b[0]+b[2]) - max(a[0], b[0])), iy = max(0, min(a[1]+a[3], b[1]+b[3]) - max(a[1], b[1]))
  return ix*iy / max(1e-6, min(a[2]*a[3], b[2]*b[3]))
}
for path in args {
  guard let img = NSImage(contentsOfFile: path), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { continue }
  let W = Double(cg.width), H = Double(cg.height)
  var items: [[String: Any]] = []
  if W > 2.5 * H && W > 1200 {
    let tw = max(Int(H) * 3, 1200), ov = 200
    var x0 = 0
    while x0 < Int(W) {
      let x1 = min(Int(W), x0 + tw)
      guard let tile = cg.cropping(to: CGRect(x: x0, y: 0, width: x1 - x0, height: Int(H))) else { break }
      for it in recognize(tile) {
        let b = it["box"] as! [Double]
        let cutL = x0 > 0 && b[0] < 4, cutR = x1 < Int(W) && b[0] + b[2] > Double(x1 - x0) - 4
        if cutL || cutR { continue }
        let s = shifted(it, Double(x0))
        if items.contains(where: { overlapRatio($0["box"] as! [Double], s["box"] as! [Double]) > 0.6 }) { continue }
        items.append(s)
      }
      if x1 >= Int(W) { break }
      x0 = x1 - ov
    }
  } else {
    items = recognize(cg)
  }
  out.append(["file": (path as NSString).lastPathComponent, "W": W, "H": H, "items": items])
}
print(String(data: try! JSONSerialization.data(withJSONObject: out), encoding: .utf8)!)
