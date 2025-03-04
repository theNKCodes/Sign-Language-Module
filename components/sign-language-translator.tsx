// "use client"

// import { useState } from "react"
// import axios from "axios"
// import { SignLanguageDisplay } from "@/components/sign-language-display"
// import { Button } from "@/components/ui/button"
// import { Textarea } from "@/components/ui/textarea"
// import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
// import { ArrowRight, Loader2, RefreshCw } from "lucide-react"

// export function SignLanguageTranslator() {
//   const [inputText, setInputText] = useState("")
//   const [submittedText, setSubmittedText] = useState("")
//   const [nlpResults, setNlpResults] = useState(null)
//   const [isTranslating, setIsTranslating] = useState(false)
//   const [isProcessing, setIsProcessing] = useState(false)

//   const handleSubmit = async () => {
//     if (inputText.trim()) {
//       setIsProcessing(true)
//       setIsTranslating(true)
//       console.log("Text submitted:", inputText)
//       setSubmittedText(inputText)
//       await processText(inputText)
//       setIsProcessing(false)
//     } else {
//       console.log("No text to submit")
//     }
//   }

//   const processText = async (text) => {
//     try {
//       console.log("Sending text to backend:", text)
//       const response = await axios.post(
//         "http://localhost:5000/process",
//         { text },
//         {
//           headers: { "Content-Type": "application/json" },
//         },
//       )
//       console.log("Received response from backend:", response.data)
//       setNlpResults(response.data)
//     } catch (error) {
//       console.error("Error processing text:", error.response ? error.response.data : error.message)
//     }
//   }

//   const handleReset = () => {
//     setInputText("")
//     setSubmittedText("")
//     setNlpResults(null)
//     setIsTranslating(false)
//   }

//   return (
//     <Card className="w-full max-w-3xl mx-auto shadow-lg">
//       <CardHeader>
//         <CardTitle className="text-2xl">Sign Language Translation</CardTitle>
//         <CardDescription>Enter text to translate into sign language videos</CardDescription>
//       </CardHeader>

//       <CardContent>
//         {!isTranslating ? (
//           <div className="space-y-4">
//             <Textarea
//               value={inputText}
//               onChange={(e) => setInputText(e.target.value)}
//               placeholder="Type your text here..."
//               className="min-h-[150px] resize-none"
//             />
//             <div className="flex justify-end">
//               <Button
//                 onClick={handleSubmit}
//                 disabled={!inputText.trim() || isProcessing}
//                 className="transition-all"
//                 size="lg"
//               >
//                 {isProcessing ? (
//                   <>
//                     <Loader2 className="mr-2 h-4 w-4 animate-spin" />
//                     Processing...
//                   </>
//                 ) : (
//                   <>
//                     Translate to Sign Language
//                     <ArrowRight className="ml-2 h-4 w-4" />
//                   </>
//                 )}
//               </Button>
//             </div>
//           </div>
//         ) : (
//           <div className="space-y-6">
//             <div className="rounded-lg bg-muted p-4">
//               <h3 className="text-sm font-medium mb-2">Translating:</h3>
//               <p className="text-lg font-medium">"{submittedText}"</p>
//             </div>

//             <div className="bg-card rounded-lg border p-4">
//               <h3 className="text-lg font-semibold mb-4">Sign Language Video</h3>
//               <SignLanguageDisplay text={submittedText} />
//             </div>
//           </div>
//         )}
//       </CardContent>

//       {isTranslating && (
//         <CardFooter className="flex justify-center">
//           <Button onClick={handleReset} variant="outline" size="lg" className="mt-4">
//             <RefreshCw className="mr-2 h-4 w-4" />
//             Translate New Text
//           </Button>
//         </CardFooter>
//       )}
//     </Card>
//   )
// }

"use client"

import { useState } from "react"
import axios from "axios"
import { SignLanguageDisplay } from "@/components/sign-language-display"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowRight, Loader2, RefreshCw, Mic, MicOff } from "lucide-react"

export function SignLanguageTranslator() {
  const [inputText, setInputText] = useState("")
  const [submittedText, setSubmittedText] = useState("")
  const [nlpResults, setNlpResults] = useState(null)
  const [isTranslating, setIsTranslating] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isListening, setIsListening] = useState(false)

  const handleSubmit = async () => {
    if (inputText.trim()) {
      setIsProcessing(true)
      setIsTranslating(true)
      console.log("Text submitted:", inputText)
      setSubmittedText(inputText)
      await processText(inputText)
      setIsProcessing(false)
    } else {
      console.log("No text to submit")
    }
  }

  const processText = async (text) => {
    try {
      console.log("Sending text to backend:", text)
      const response = await axios.post(
        "http://localhost:5000/process",
        { text },
        {
          headers: { "Content-Type": "application/json" },
        },
      )
      console.log("Received response from backend:", response.data)
      setNlpResults(response.data)
    } catch (error) {
      console.error("Error processing text:", error.response ? error.response.data : error.message)
    }
  }

  const handleReset = () => {
    setInputText("")
    setSubmittedText("")
    setNlpResults(null)
    setIsTranslating(false)
  }

  // Speech Recognition (Web Speech API)
  const startListening = () => {
    if (!("webkitSpeechRecognition" in window)) {
      alert("Speech recognition is not supported in your browser.")
      return
    }

    const recognition = new window.webkitSpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = false
    recognition.lang = "en-US"

    recognition.onstart = () => {
      setIsListening(true)
    }

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      console.log("Recognized speech:", transcript)
      setInputText(transcript)
    }

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognition.start()
  }

  return (
    <Card className="w-full max-w-3xl mx-auto shadow-lg">
      <CardHeader>
        <CardTitle className="text-2xl">Sign Language Translation</CardTitle>
        <CardDescription>Enter text or speak to translate into sign language videos</CardDescription>
      </CardHeader>

      <CardContent>
        {!isTranslating ? (
          <div className="space-y-4">
            <div className="relative">
              <Textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Type or speak your text here..."
                className="min-h-[150px] resize-none pr-12"
              />
              <button
                type="button"
                onClick={startListening}
                className="absolute right-3 top-3 text-gray-500 hover:text-gray-900"
              >
                {isListening ? <MicOff size={24} /> : <Mic size={24} />}
              </button>
            </div>

            <div className="flex justify-end">
              <Button
                onClick={handleSubmit}
                disabled={!inputText.trim() || isProcessing}
                className="transition-all"
                size="lg"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    Translate to Sign Language
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="rounded-lg bg-muted p-4">
              <h3 className="text-sm font-medium mb-2">Translating:</h3>
              <p className="text-lg font-medium">"{submittedText}"</p>
            </div>

            <div className="bg-card rounded-lg border p-4">
              <h3 className="text-lg font-semibold mb-4">Sign Language Video</h3>
              <SignLanguageDisplay text={submittedText} />
            </div>
          </div>
        )}
      </CardContent>

      {isTranslating && (
        <CardFooter className="flex justify-center">
          <Button onClick={handleReset} variant="outline" size="lg" className="mt-4">
            <RefreshCw className="mr-2 h-4 w-4" />
            Translate New Text
          </Button>
        </CardFooter>
      )}
    </Card>
  )
}
