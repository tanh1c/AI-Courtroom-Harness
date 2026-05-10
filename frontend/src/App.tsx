/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect } from 'react';
import { 
  Bell, 
  ChevronRight, 
  ChevronDown, 
  Search, 
  Save, 
  Layout,
  Briefcase,
  BookOpen,
  Bot,
  Settings,
  MoreVertical,
  Play,
  Pause,
  ShieldAlert,
  Scale,
  Maximize2,
  FileText,
  MessageSquare,
  ShieldCheck,
  X,
  FileDown,
  Bookmark,
  CheckCircle2,
  Scale3d,
  UserCheck,
  Moon,
  Sun
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';

export default function App() {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isLeftSidebarOpen, setIsLeftSidebarOpen] = useState(true);
  const [isRightSidebarOpen, setIsRightSidebarOpen] = useState(true);

  useEffect(() => {
    if (document.documentElement.classList.contains('dark')) {
      setIsDarkMode(true);
    }
  }, []);

  const toggleDarkMode = () => {
    if (isDarkMode) {
      document.documentElement.classList.remove('dark');
      setIsDarkMode(false);
    } else {
      document.documentElement.classList.add('dark');
      setIsDarkMode(true);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background text-foreground overflow-hidden font-sans">
      {/* Top Header */}
      <header className="h-16 border-b border-border flex items-center justify-between px-4 shrink-0 bg-background/95 backdrop-blur z-10 relative">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3 text-primary font-serif font-bold leading-[1.1] uppercase tracking-widest pl-2">
            <Scale3d className="w-9 h-9" />
            <div className="flex flex-col pt-1">
              <span className="text-xl">AI Courtroom</span>
              <span className="text-[12px] tracking-[0.4em] text-primary/70 font-sans">Harness</span>
            </div>
          </div>
          <Separator orientation="vertical" className="h-8 mx-4" />
          <div className="flex flex-col">
            <h1 className="text-sm font-semibold">Tranh chấp hợp đồng vay tài sản</h1>
            <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
              <span>Số: 12/2024/TLST-DS</span>
              <Badge variant="secondary" className="bg-muted text-muted-foreground hover:bg-muted font-normal h-5 border border-border/50">Đang xử lý</Badge>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" className="h-9 gap-2 border-border/50 bg-background hover:bg-accent/50 text-muted-foreground font-normal">
            <Save className="w-4 h-4" /> Lưu
          </Button>
          <Button size="sm" className="h-9 gap-2 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold border-none rounded">
            <FileText className="w-4 h-4" /> Tạo báo cáo <ChevronDown className="w-4 h-4 opacity-70" />
          </Button>
          <Button variant="ghost" size="icon" onClick={toggleDarkMode} className="h-9 w-9 text-muted-foreground hover:bg-accent/50 group">
             {isDarkMode ? <Sun className="w-4 h-4 group-hover:text-primary transition-colors" /> : <Moon className="w-4 h-4 group-hover:text-primary transition-colors" />}
          </Button>
          <Button variant="ghost" size="icon" className="h-9 w-9 text-muted-foreground hover:bg-accent/50 group relative">
            <Bell className="w-4 h-4 group-hover:text-primary transition-colors" />
            <span className="absolute top-2 right-2 w-1.5 h-1.5 bg-destructive rounded-full border border-background"></span>
          </Button>
          <Separator orientation="vertical" className="h-6 mx-1" />
          <div className="flex items-center gap-3 pl-2">
            <Avatar className="h-8 w-8 ring-1 ring-border/50">
              <AvatarImage src="https://i.pravatar.cc/150?u=a042581f4e29026704d" alt="User" />
              <AvatarFallback className="bg-muted text-xs">NV</AvatarFallback>
            </Avatar>
            <div className="flex flex-col hidden sm:flex">
              <span className="text-sm font-medium leading-none">Nguyễn Văn A</span>
              <span className="text-[10px] text-muted-foreground mt-1">Thẩm phán</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden relative">
        
        {/* Left Sidebar */}
        <aside className={`${isLeftSidebarOpen ? 'w-72 border-r' : 'w-0 border-r-0'} border-border bg-card/30 flex flex-col shrink-0 transition-all duration-300 relative z-20`}>
          <div className={`w-72 flex flex-col h-full overflow-hidden transition-opacity duration-300 ${isLeftSidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
            <div className="p-3 border-b border-border/50 shrink-0">
              <Button variant="ghost" onClick={() => setIsLeftSidebarOpen(false)} className="w-full justify-between text-muted-foreground hover:text-foreground h-9 font-normal">
                <div className="flex items-center gap-2">
                  <ChevronRight className="w-4 h-4 rotate-180" /> Thu gọn
                </div>
                <ChevronRight className="w-3 h-3 opacity-50" />
              </Button>
            </div>
            
            <ScrollArea className="flex-1">
              <div className="p-3 space-y-1 w-72">
              <Collapsible defaultOpen>
                <CollapsibleTrigger className="flex items-center justify-between w-full p-2 text-sm font-medium hover:bg-accent rounded-md group">
                  <div className="flex items-center gap-2 text-primary">
                    <FileText className="w-4 h-4" />
                    <span className="uppercase tracking-wide text-xs font-semibold">Tóm tắt vụ án</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <span className="text-xs bg-muted px-1.5 py-0.5 rounded-sm">5</span>
                    <ChevronDown className="w-3 h-3 group-data-[state=open]:rotate-180 transition-transform" />
                  </div>
                </CollapsibleTrigger>
                <CollapsibleContent className="pt-2 pb-4 space-y-3 px-2">
                  <div className="grid grid-cols-[80px_1fr] gap-2 text-sm">
                    <span className="text-muted-foreground">Nguyên đơn</span>
                    <span className="font-medium text-foreground text-right">Ông Trần Văn Nam</span>
                  </div>
                  <div className="grid grid-cols-[80px_1fr] gap-2 text-sm">
                    <span className="text-muted-foreground">Bị đơn</span>
                    <span className="font-medium text-foreground text-right">Ông Lê Văn Hùng</span>
                  </div>
                  <Separator className="bg-border/50" />
                  <div className="flex flex-col gap-1 text-sm">
                    <span className="text-muted-foreground">Loại tranh chấp</span>
                    <span className="font-medium text-foreground">Tranh chấp hợp đồng vay tài sản</span>
                  </div>
                  <div className="flex flex-col gap-1 text-sm">
                    <span className="text-muted-foreground">Giá trị tài sản tranh chấp</span>
                    <span className="font-medium text-primary">500.000.000 VNĐ</span>
                  </div>
                  <div className="flex flex-col gap-1 text-sm">
                    <span className="text-muted-foreground">Tòa án</span>
                    <span className="font-medium text-foreground">TAND Quận 1,<br/>TP. Hồ Chí Minh</span>
                  </div>
                  <Button variant="outline" size="sm" className="w-full mt-2 border-border/50">Xem chi tiết</Button>
                </CollapsibleContent>
              </Collapsible>

              <Separator className="bg-border/30 my-2" />

              <Collapsible>
                <CollapsibleTrigger className="flex items-center justify-between w-full p-2 text-sm font-medium hover:bg-accent rounded-md text-muted-foreground group">
                  <div className="flex items-center gap-2">
                    <Scale className="w-4 h-4" />
                    <span className="uppercase tracking-wide text-xs font-semibold">Chứng cứ</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs bg-muted px-1.5 py-0.5 rounded-sm">5</span>
                    <ChevronDown className="w-3 h-3 group-data-[state=open]:rotate-180 transition-transform" />
                  </div>
                </CollapsibleTrigger>
              </Collapsible>

              <Collapsible>
                <CollapsibleTrigger className="flex items-center justify-between w-full p-2 text-sm font-medium hover:bg-accent rounded-md text-muted-foreground group">
                  <div className="flex items-center gap-2">
                    <BookOpen className="w-4 h-4" />
                    <span className="uppercase tracking-wide text-xs font-semibold">Vấn đề pháp lý</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs bg-muted px-1.5 py-0.5 rounded-sm">3</span>
                    <ChevronDown className="w-3 h-3 group-data-[state=open]:rotate-180 transition-transform" />
                  </div>
                </CollapsibleTrigger>
              </Collapsible>

              <Collapsible>
                <CollapsibleTrigger className="flex items-center justify-between w-full p-2 text-sm font-medium hover:bg-accent rounded-md text-muted-foreground group">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="w-4 h-4" />
                    <span className="uppercase tracking-wide text-xs font-semibold">Yêu cầu của các bên</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs bg-muted px-1.5 py-0.5 rounded-sm">2</span>
                    <ChevronDown className="w-3 h-3 group-data-[state=open]:rotate-180 transition-transform" />
                  </div>
                </CollapsibleTrigger>
              </Collapsible>
            </div>
          </ScrollArea>
          
          <div className="border-t border-border/50 p-2 grid grid-cols-4 gap-1 bg-background/50">
            <Button variant="ghost" className="flex flex-col gap-1 h-auto py-2 px-1 text-muted-foreground hover:text-primary">
              <Briefcase className="w-4 h-4" />
              <span className="text-[10px]">Hồ sơ vụ án</span>
            </Button>
            <Button variant="ghost" className="flex flex-col gap-1 h-auto py-2 px-1 text-muted-foreground hover:text-primary">
              <BookOpen className="w-4 h-4" />
              <span className="text-[10px]">Thư viện</span>
            </Button>
            <Button variant="ghost" className="flex flex-col gap-1 h-auto py-2 px-1 text-primary bg-primary/5">
              <Bot className="w-4 h-4" />
              <span className="text-[10px]">Trợ lý AI</span>
            </Button>
            <Button variant="ghost" className="flex flex-col gap-1 h-auto py-2 px-1 text-muted-foreground hover:text-primary">
              <Settings className="w-4 h-4" />
              <span className="text-[10px]">Cài đặt</span>
            </Button>
          </div>
          </div>

          {!isLeftSidebarOpen && (
             <Button 
               variant="outline" 
               size="icon" 
               onClick={() => setIsLeftSidebarOpen(true)}
               className="absolute top-3 -right-3 sm:-right-4 translate-x-full z-50 h-8 w-8 rounded-full shadow-md bg-background border-border text-foreground hover:bg-muted"
             >
               <ChevronRight className="w-4 h-4" />
             </Button>
          )}
        </aside>

        {/* Center Main Stage */}
        <main className="flex-1 flex flex-col min-w-0 p-4 pb-20 relative bg-background">
            
            <Card className="flex-1 flex flex-col shadow-xl overflow-hidden relative z-10 rounded-xl border-none">
              {/* Fake paper background */}
              <div className="absolute inset-0 bg-background z-0"></div>
              {/* Paper texture noise (optional but adds to the look) */}
              <div className="absolute inset-0 opacity-[0.01] mix-blend-multiply z-0" style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`}}></div>

              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-border relative z-10 bg-muted/30 text-foreground">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center text-primary">
                    <Scale3d className="w-5 h-5" />
                  </div>
                  <h2 className="text-lg font-serif font-bold tracking-wide uppercase text-foreground">Biên bản phiên tòa <span className="text-primary font-sans text-[10px] tracking-normal ml-2 font-medium bg-primary/10 px-2 py-0.5 rounded-full relative top-[-2px] uppercase pb-[3px]">• Trực tiếp</span></h2>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" className="h-8 text-xs font-medium border-border bg-background/50 hover:bg-muted text-foreground">
                    <Maximize2 className="w-3.5 h-3.5 mr-2" /> Xem toàn bộ tiến trình
                  </Button>
                  <Button variant="outline" size="icon" className="h-8 w-8 border-border bg-background/50 hover:bg-muted text-foreground">
                    <Settings className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Stepper */}
              <div className="flex items-center p-0 border-b border-border select-none relative h-[72px] z-10 text-foreground">
                 <div className="absolute top-[20px] left-12 right-12 h-[2px] bg-border z-0"></div>
                 <div className="absolute top-[20px] left-12 w-[35%] h-[2px] bg-primary z-0"></div>
                 
                 <div className="flex-1 flex flex-col items-center justify-center relative z-10 h-full cursor-pointer group pt-1">
                    <div className="w-8 h-8 bg-primary border-2 border-primary rounded-full flex items-center justify-center text-primary-foreground text-sm font-medium mb-1 z-10 shadow-sm">1</div>
                    <span className="text-[10px] font-bold tracking-wider uppercase text-foreground">Mở phiên</span>
                    <span className="text-[10px] text-muted-foreground mt-0.5">09:00</span>
                 </div>
                 
                 <div className="flex-1 flex flex-col items-center justify-center relative z-10 h-full pt-1">
                    <div className="absolute inset-x-2 bottom-0 top-[2px] bg-primary/5 rounded-t-lg z-0"></div>
                    <div className="absolute inset-x-2 top-0 h-[3px] bg-primary rounded-t-lg z-0"></div>
                    
                    <div className="w-8 h-8 bg-background border-2 border-primary rounded-full flex items-center justify-center text-primary text-sm font-bold mb-1 z-10">2</div>
                    <span className="text-[10px] font-bold tracking-wider uppercase text-primary relative z-10">Tranh tụng</span>
                    <span className="text-[10px] text-primary/70 font-medium relative z-10 mt-0.5">09:15</span>
                 </div>
                 
                 <div className="flex-1 flex flex-col items-center justify-center relative z-10 h-full opacity-50 cursor-pointer hover:opacity-100 transition-opacity pt-1">
                    <div className="w-8 h-8 bg-background border-2 border-border text-muted-foreground rounded-full flex items-center justify-center text-sm font-medium mb-1 z-10">3</div>
                    <span className="text-[10px] font-bold tracking-wider uppercase text-foreground">Nhận định sơ bộ</span>
                    <span className="text-[10px] text-muted-foreground mt-0.5">10:30</span>
                 </div>
                 
                 <div className="flex-1 flex flex-col items-center justify-center relative z-10 h-full opacity-50 cursor-pointer hover:opacity-100 transition-opacity pt-1">
                    <div className="w-8 h-8 bg-background border-2 border-border text-muted-foreground rounded-full flex items-center justify-center text-sm font-medium mb-1 z-10">4</div>
                    <span className="text-[10px] font-bold tracking-wider uppercase text-foreground">Kết thúc phiên</span>
                    <span className="text-[10px] text-muted-foreground mt-0.5">10:45</span>
                 </div>
              </div>

              {/* Transcript Area */}
              <ScrollArea className="flex-1 p-6 px-10 relative z-10">
                 <div className="absolute left-[83px] top-8 bottom-6 w-px bg-border"></div>
                 
                 <div className="space-y-8 relative z-10 max-w-4xl mx-auto">
                    {/* Item 1 */}
                    <div className="flex gap-4 group">
                      <div className="w-12 text-right pt-1 shrink-0">
                        <span className="text-xs text-muted-foreground font-mono">09:15</span>
                      </div>
                      <div className="w-8 h-8 rounded-full bg-blue-500/10 text-blue-500 border border-blue-500/20 flex items-center justify-center shrink-0 relative mt-0.5">
                         <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center">
                            <span className="text-[12px] font-bold">N</span>
                         </div>
                         <div className="absolute -left-[24px] top-1/2 w-[22px] h-px bg-blue-500/30"></div>
                         <div className="absolute -left-[26px] top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-blue-500"></div>
                      </div>
                      <div className="flex-1 pt-1 pb-4">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="text-[13px] font-bold text-blue-600 uppercase tracking-wide">Nguyên đơn <span className="text-muted-foreground font-normal normal-case tracking-normal ml-1">– Trình bày yêu cầu</span></h4>
                          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground"><Bookmark className="w-3.5 h-3.5" /></Button>
                            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground"><CheckCircle2 className="w-3.5 h-3.5" /></Button>
                            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground"><MoreVertical className="w-3.5 h-3.5" /></Button>
                          </div>
                        </div>
                        <p className="text-[13px] text-foreground/90 leading-[1.6] mb-2"><span className="font-semibold text-foreground">Bị đơn:</span> Trình bày yêu cầu, đưa ra chứng cứ, phân tích một phần yêu cầu.</p>
                        <p className="text-[13px] text-foreground/90 leading-[1.6]"><span className="font-semibold text-foreground">HĐXX:</span> Hỏi – Đáp các bên.</p>
                      </div>
                    </div>

                    {/* Item 2 */}
                    <div className="flex gap-4 group">
                      <div className="w-12 text-right pt-1 shrink-0">
                        <span className="text-xs text-muted-foreground font-mono">09:22</span>
                      </div>
                      <div className="w-8 h-8 rounded-full bg-amber-500/10 text-amber-500 border border-amber-500/20 flex items-center justify-center shrink-0 relative mt-0.5 z-10">
                         <div className="w-6 h-6 rounded-full bg-amber-500/20 flex items-center justify-center">
                            <span className="text-[12px] font-bold">B</span>
                         </div>
                      </div>
                      <div className="flex-1 pt-1 pb-4">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="text-[13px] font-bold text-amber-600 uppercase tracking-wide">Bị đơn <span className="text-muted-foreground font-normal normal-case tracking-normal ml-1">– Trình bày ý kiến</span></h4>
                          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground"><Bookmark className="w-3.5 h-3.5" /></Button>
                            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground"><CheckCircle2 className="w-3.5 h-3.5" /></Button>
                            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground"><MoreVertical className="w-3.5 h-3.5" /></Button>
                          </div>
                        </div>
                        <p className="text-[13px] text-foreground/90 leading-[1.6] mb-2"><span className="font-semibold text-foreground">Bị đơn:</span> Trình bày ý kiến, đưa ra chứng cứ, phản đối một phần yêu cầu.</p>
                        <p className="text-[13px] text-foreground/90 leading-[1.6]"><span className="font-semibold text-foreground">Kiểm sát viên:</span> Phát biểu ý kiến.</p>
                      </div>
                    </div>

                    {/* Item 3 */}
                    <div className="flex gap-4 group">
                      <div className="w-12 text-right pt-1 shrink-0">
                        <span className="text-xs text-muted-foreground font-mono">09:28</span>
                      </div>
                      <div className="w-8 h-8 rounded-full bg-primary/10 text-primary border border-primary/20 flex items-center justify-center shrink-0 relative mt-0.5 z-10 shadow-[0_0_10px_rgba(37,99,235,0.1)]">
                         <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center">
                            <Scale className="w-3.5 h-3.5" />
                         </div>
                      </div>
                      <div className="flex-1 pt-1 pb-4">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="text-[13px] font-bold text-primary uppercase tracking-wide">HĐXX <span className="text-muted-foreground font-normal normal-case tracking-normal ml-1">– Hỏi đáp các bên</span></h4>
                          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground"><Bookmark className="w-3.5 h-3.5" /></Button>
                            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground"><CheckCircle2 className="w-3.5 h-3.5" /></Button>
                            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground"><MoreVertical className="w-3.5 h-3.5" /></Button>
                          </div>
                        </div>
                        <p className="text-[13px] text-foreground/90 leading-[1.6] mb-2"><span className="font-semibold text-foreground">Thẩm phán:</span> Đặt câu hỏi để làm rõ nội dung tranh chấp.</p>
                        <p className="text-[13px] text-foreground/90 leading-[1.6]"><span className="font-semibold text-foreground">Các bên:</span> Trả lời theo yêu cầu của HĐXX.</p>
                      </div>
                    </div>
                    
                    {/* Item 4 */}
                    <div className="flex gap-4 group">
                      <div className="w-12 text-right pt-1 shrink-0">
                        <span className="text-xs text-muted-foreground font-mono">09:35</span>
                      </div>
                      <div className="w-8 h-8 rounded-full bg-purple-500/10 text-purple-600 border border-purple-500/20 flex items-center justify-center shrink-0 relative mt-0.5 z-10">
                         <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center">
                            <span className="text-[12px] font-bold">K</span>
                         </div>
                      </div>
                      <div className="flex-1 pt-1 pb-4">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="text-[13px] font-bold text-purple-600 uppercase tracking-wide">Kiểm sát viên <span className="text-muted-foreground font-normal normal-case tracking-normal ml-1">– Phát biểu ý kiến</span></h4>
                          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground"><Bookmark className="w-3.5 h-3.5" /></Button>
                            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground"><CheckCircle2 className="w-3.5 h-3.5" /></Button>
                            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground"><MoreVertical className="w-3.5 h-3.5" /></Button>
                          </div>
                        </div>
                        <p className="text-[13px] text-foreground/90 leading-[1.6]"><span className="font-semibold text-foreground">Kiểm sát viên:</span> Phát biểu ý kiến về việc tuân theo pháp luật trong quá trình giải quyết vụ án.</p>
                      </div>
                    </div>

                    {/* Item 5 */}
                    <div className="flex gap-4 group pb-4">
                      <div className="w-12 text-right pt-1 shrink-0">
                        <span className="text-xs text-muted-foreground font-mono">09:40</span>
                      </div>
                      <div className="w-8 h-8 rounded-full bg-slate-500/10 text-slate-600 border border-slate-500/20 flex items-center justify-center shrink-0 relative mt-0.5 z-10">
                         <div className="w-6 h-6 rounded-full bg-slate-500/20 flex items-center justify-center">
                            <span className="text-[12px] font-bold">T</span>
                         </div>
                      </div>
                      <div className="flex-1 pt-1">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="text-[13px] font-bold text-slate-600 uppercase tracking-wide">Thư ký <span className="text-muted-foreground font-normal normal-case tracking-normal ml-1">– Ghi nhận</span></h4>
                          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground"><Bookmark className="w-3.5 h-3.5" /></Button>
                            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground"><CheckCircle2 className="w-3.5 h-3.5" /></Button>
                            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground"><MoreVertical className="w-3.5 h-3.5" /></Button>
                          </div>
                        </div>
                        <p className="text-[13px] text-foreground/90 leading-[1.6]"><span className="font-semibold text-foreground">Thư ký:</span> Ghi nhận toàn bộ diễn biến phiên tòa, lời trình bày và tài liệu được đưa ra.</p>
                      </div>
                    </div>
                 </div>
              </ScrollArea>

              {/* Judge's Assessment Panel */}
              <div className="p-4 bg-muted/50 border-t border-border relative overflow-hidden z-20 m-0 rounded-b-xl border-none">
                <div className="absolute top-0 left-0 right-0 h-[30px] bg-gradient-to-b from-primary/5 to-transparent"></div>
                <div className="flex items-center gap-2 mb-3 relative z-10">
                  <Scale className="w-4 h-4 text-primary" />
                  <h3 className="text-sm font-semibold tracking-wider uppercase text-primary">Nhận định của Thẩm phán</h3>
                </div>
                
                <div className="grid grid-cols-3 gap-4 mb-4 relative z-10">
                  {/* Col 1 */}
                  <div className="bg-background border border-border rounded-lg p-3 px-4 shadow-sm">
                    <h4 className="text-[11px] font-semibold text-foreground/80 mb-3 uppercase tracking-wider">Tóm tắt tranh tụng</h4>
                    <ul className="space-y-3 text-xs text-muted-foreground leading-relaxed">
                      <li className="flex gap-2 items-start"><CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" /> <span>Các bên đã trình bày đầy đủ yêu cầu và ý kiến.</span></li>
                      <li className="flex gap-2 items-start"><CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" /> <span>Một số chứng cứ cần được xác minh thêm.</span></li>
                      <li className="flex gap-2 items-start">
                         <div className="w-4 h-4 rounded-full border border-primary flex items-center justify-center shrink-0 mt-0.5"><div className="w-1.5 h-1.5 bg-primary rounded-full"></div></div> 
                         <span>Chưa thống nhất về khoản vay và thời điểm vay.</span>
                      </li>
                    </ul>
                  </div>
                  {/* Col 2 */}
                  <div className="bg-background border border-border rounded-lg p-3 px-4 flex flex-col shadow-sm">
                    <div className="flex items-center gap-2 mb-3">
                       <h4 className="text-[11px] font-semibold text-foreground/80 uppercase tracking-wider">Đề xuất AI</h4>
                       <span className="bg-muted text-muted-foreground text-[9px] px-1.5 py-0.5 rounded uppercase tracking-wider border border-border font-bold">AI</span>
                    </div>
                    <ul className="space-y-3 text-xs text-muted-foreground leading-relaxed flex-1">
                      <li className="flex gap-2 items-start"><CheckCircle2 className="w-4 h-4 text-muted-foreground/50 shrink-0 mt-0.5" /> <span>Xác minh hợp đồng vay và biên nhận.</span></li>
                      <li className="flex gap-2 items-start"><CheckCircle2 className="w-4 h-4 text-muted-foreground/50 shrink-0 mt-0.5" /> <span>Đối chiếu chứng cứ thanh toán (nếu có).</span></li>
                      <li className="flex gap-2 items-start"><CheckCircle2 className="w-4 h-4 text-muted-foreground/50 shrink-0 mt-0.5" /> <span>Làm rõ lãi suất và thời điểm vay.</span></li>
                    </ul>
                    <Button variant="link" className="text-primary text-[11px] h-auto p-0 mt-2 font-medium justify-start hover:text-primary/80">
                       Xem chi tiết đề xuất <ChevronRight className="w-3 h-3 ml-1" />
                    </Button>
                  </div>
                  {/* Col 3 */}
                  <div className="flex flex-col">
                    <h4 className="text-[11px] font-semibold text-foreground/80 mb-3 uppercase tracking-wider">Ghi chú của thẩm phán</h4>
                    <textarea 
                      className="flex-1 w-full bg-background border border-border rounded-lg p-3 text-sm text-foreground placeholder:text-muted-foreground resize-none focus:outline-none focus:border-primary/50 transition-colors shadow-sm"
                      placeholder="Nhập ghi chú hoặc nhận định sơ bộ..."
                    ></textarea>
                     <div className="text-[10px] text-muted-foreground text-right mt-1.5">0/1000</div>
                  </div>
                </div>

                <div className="flex gap-4 relative z-10">
                  <Button className="w-[180px] gap-2 bg-primary hover:bg-primary/90 text-primary-foreground font-bold border-none shadow-md shadow-primary/20">
                    <Play className="w-4 h-4 fill-current" /> Tiếp tục phiên
                  </Button>
                  <Button variant="outline" className="flex-1 gap-2 bg-background hover:bg-muted text-foreground font-medium transition-colors border-border">
                    <Pause className="w-4 h-4 fill-current opacity-70" /> Tạm dừng
                  </Button>
                  <Button variant="outline" className="flex-1 gap-2 bg-background hover:bg-muted text-foreground font-medium transition-colors border-border group">
                    <ShieldCheck className="w-4 h-4 text-primary group-hover:scale-110 transition-transform" /> Xác minh
                  </Button>
                  <Button variant="outline" className="flex-1 gap-2 bg-background hover:bg-muted text-foreground font-medium transition-colors border-border group">
                    <Scale className="w-4 h-4 text-primary group-hover:scale-110 transition-transform" /> Tạo nhận định
                  </Button>
                </div>
              </div>
            </Card>
        </main>

        {/* Right Sidebar */}
        <aside className={`${isRightSidebarOpen ? 'w-80 border-l' : 'w-0 border-l-0'} border-border bg-card/30 flex flex-col shrink-0 transition-all duration-300 relative z-20`}>
          <div className={`w-80 flex flex-col h-full overflow-hidden transition-opacity duration-300 ${isRightSidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
            <div className="p-3 border-b border-border/50 shrink-0">
              <Button variant="ghost" onClick={() => setIsRightSidebarOpen(false)} className="w-full justify-between text-muted-foreground hover:text-foreground h-9 font-normal">
                <div className="flex items-center gap-2">
                  <ChevronRight className="w-4 h-4" /> Thu gọn
                </div>
              </Button>
            </div>
            
            <ScrollArea className="flex-1">
              <div className="p-3 space-y-3 w-80">
              {/* Citadel/Legal Citations */}
              <Card className="bg-background border-border/50 overflow-hidden shadow-sm">
                 <Collapsible defaultOpen className="flex flex-col">
                    <CollapsibleTrigger className="flex items-center justify-between w-full p-3 hover:bg-accent/50 transition-colors">
                       <div className="flex items-center gap-2 text-primary">
                          <BookOpen className="w-4 h-4" />
                          <span className="uppercase tracking-wide text-xs font-semibold">Trích dẫn pháp luật</span>
                       </div>
                       <div className="flex items-center gap-2 text-muted-foreground">
                          <span className="text-xs bg-muted px-1.5 py-0.5 rounded-sm">4</span>
                          <ChevronDown className="w-3 h-3 transition-transform" />
                       </div>
                    </CollapsibleTrigger>
                    <CollapsibleContent className="p-3 pt-0 space-y-3">
                       <div className="flex gap-3 group">
                          <div className="w-8 h-8 rounded bg-red-900/10 text-red-500 border border-red-900/20 flex items-center justify-center shrink-0">
                            <BookOpen className="w-4 h-4" />
                          </div>
                          <div className="flex-1 min-w-0">
                             <div className="flex items-center justify-between">
                               <h5 className="text-sm font-semibold truncate text-foreground/90">Điều 463 Bộ luật Dân sự 2015</h5>
                             </div>
                             <p className="text-xs text-muted-foreground truncate mb-1">Hợp đồng vay tài sản</p>
                             <Badge variant="outline" className="text-[9px] px-1.5 py-0 h-4 border-green-500/30 text-green-500 bg-green-500/5">Đã xác minh</Badge>
                          </div>
                       </div>
                       
                       <div className="flex gap-3 group">
                          <div className="w-8 h-8 rounded bg-red-900/10 text-red-500 border border-red-900/20 flex items-center justify-center shrink-0">
                            <BookOpen className="w-4 h-4" />
                          </div>
                          <div className="flex-1 min-w-0">
                             <h5 className="text-sm font-semibold truncate text-foreground/90">Điều 466 Bộ luật Dân sự 2015</h5>
                             <p className="text-xs text-muted-foreground truncate mb-1">Nghĩa vụ trả nợ</p>
                             <Badge variant="outline" className="text-[9px] px-1.5 py-0 h-4 border-green-500/30 text-green-500 bg-green-500/5">Đã xác minh</Badge>
                          </div>
                       </div>

                       <div className="flex gap-3 group">
                          <div className="w-8 h-8 rounded bg-red-900/10 text-red-500 border border-red-900/20 flex items-center justify-center shrink-0">
                            <BookOpen className="w-4 h-4" />
                          </div>
                          <div className="flex-1 min-w-0">
                             <h5 className="text-sm font-semibold truncate text-foreground/90">Điều 357 Bộ luật Dân sự 2015</h5>
                             <p className="text-xs text-muted-foreground truncate mb-1">Lãi suất</p>
                             <Badge variant="outline" className="text-[9px] px-1.5 py-0 h-4 border-green-500/30 text-green-500 bg-green-500/5">Đã xác minh</Badge>
                          </div>
                       </div>

                       <div className="flex gap-3 group">
                          <div className="w-8 h-8 rounded bg-red-900/10 text-red-500 border border-red-900/20 flex items-center justify-center shrink-0">
                            <BookOpen className="w-4 h-4" />
                          </div>
                          <div className="flex-1 min-w-0">
                             <h5 className="text-sm font-semibold truncate text-foreground/90">Nghị quyết 01/2019/NQ-HĐTP</h5>
                             <p className="text-xs text-muted-foreground truncate mb-1">Hướng dẫn áp dụng BL luật Dân sự...</p>
                             <Badge variant="outline" className="text-[9px] px-1.5 py-0 h-4 border-green-500/30 text-green-500 bg-green-500/5">Đã xác minh</Badge>
                          </div>
                       </div>

                       <Button variant="link" className="w-full text-xs text-muted-foreground mt-2 pb-0 justify-end h-auto p-0">Xem tất cả <ChevronRight className="w-3 h-3 ml-1" /></Button>
                    </CollapsibleContent>
                 </Collapsible>
              </Card>

              {/* Audit */}
              <Collapsible>
                <CollapsibleTrigger className="flex items-center justify-between w-full p-3 bg-background border border-border/50 hover:bg-accent/50 rounded-lg transition-colors group">
                  <div className="flex items-center gap-2 text-muted-foreground group-hover:text-primary transition-colors">
                    <ShieldAlert className="w-4 h-4" />
                    <span className="uppercase tracking-wide text-xs font-semibold">Kiểm toán & Rà soát</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <span className="text-xs bg-muted px-1.5 py-0.5 rounded-sm">3</span>
                    <ChevronDown className="w-3 h-3 group-data-[state=open]:rotate-180 transition-transform" />
                  </div>
                </CollapsibleTrigger>
              </Collapsible>

              {/* Human Review */}
              <Collapsible>
                <CollapsibleTrigger className="flex items-center justify-between w-full p-3 bg-background border border-border/50 hover:bg-accent/50 rounded-lg transition-colors group">
                  <div className="flex items-center gap-2 text-muted-foreground group-hover:text-primary transition-colors">
                    <UserCheck className="w-4 h-4" />
                    <span className="uppercase tracking-wide text-xs font-semibold">Rà soát của con người</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <span className="text-xs bg-muted px-1.5 py-0.5 rounded-sm">1</span>
                    <ChevronDown className="w-3 h-3 group-data-[state=open]:rotate-180 transition-transform" />
                  </div>
                </CollapsibleTrigger>
              </Collapsible>

              {/* Verification Flags */}
              <Card className="bg-background border-border/50 p-4 shadow-sm">
                 <div className="flex items-center gap-2 text-primary mb-4">
                    <Scale className="w-4 h-4" />
                    <span className="uppercase tracking-wide text-xs font-semibold">Cờ xác minh / Trạng thái</span>
                 </div>
                 
                 <div className="space-y-3 text-sm">
                    <div className="flex justify-between items-center group cursor-pointer">
                       <div className="flex items-center gap-2">
                         <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50 flex items-center justify-center">
                            <CheckCircle2 className="w-2 h-2 text-green-500" />
                         </div>
                         <span className="text-muted-foreground group-hover:text-foreground transition-colors">Đã xác minh</span>
                       </div>
                       <span className="bg-muted px-2 py-0.5 rounded text-xs">12</span>
                    </div>
                    <div className="flex justify-between items-center group cursor-pointer">
                       <div className="flex items-center gap-2">
                         <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50 flex items-center justify-center relative">
                            <span className="w-1.5 h-1.5 bg-yellow-500 rounded-full"></span>
                         </div>
                         <span className="text-foreground font-medium group-hover:underline">Chờ xác minh</span>
                       </div>
                       <span className="bg-primary/10 text-primary px-2 py-0.5 rounded text-xs font-medium border border-primary/20">5</span>
                    </div>
                    <div className="flex justify-between items-center group cursor-pointer">
                       <div className="flex items-center gap-2">
                         <div className="w-3 h-3 rounded-full bg-zinc-500/20 border border-zinc-500/50 flex items-center justify-center">
                            <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full"></span>
                         </div>
                         <span className="text-muted-foreground group-hover:text-foreground transition-colors">Chưa phân loại</span>
                       </div>
                       <span className="bg-muted px-2 py-0.5 rounded text-xs">2</span>
                    </div>
                 </div>
                 
                 <Separator className="my-3 bg-border/50" />
                 
                 <div className="flex justify-between items-center text-sm font-semibold">
                    <span className="text-foreground">Tổng cộng</span>
                    <span>19</span>
                 </div>
              </Card>

            </div>
          </ScrollArea>
          </div>

          {!isRightSidebarOpen && (
             <Button 
               variant="outline" 
               size="icon" 
               onClick={() => setIsRightSidebarOpen(true)}
               className="absolute top-3 -left-3 sm:-left-4 -translate-x-full h-8 w-8 rounded-full shadow-md bg-background border-border text-foreground hover:bg-muted"
             >
               <ChevronRight className="w-4 h-4 rotate-180" />
             </Button>
          )}
        </aside>

        {/* Bottom Banner - Report Preview */}
        <div className="absolute bottom-4 left-4 right-4 bg-background border border-border shadow-xl rounded-lg p-3 flex items-center justify-between z-20 text-foreground">
           <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-muted-foreground" />
                <span className="font-semibold text-sm uppercase tracking-wide">Xem trước báo cáo</span>
                <Badge variant="secondary" className="bg-blue-500/10 text-blue-600 border-none text-[10px] font-medium h-5 ml-1">Bản nháp</Badge>
              </div>
              
              <div className="h-6 w-px bg-border mx-2"></div>
              
              <div className="flex items-center gap-2 text-[11px] font-semibold text-muted-foreground uppercase tracking-widest">
                 <div className="flex items-center gap-2 text-green-600">
                    <div className="w-4 h-4 rounded-full bg-green-600 flex items-center justify-center text-white"><CheckCircle2 className="w-3 h-3" /></div>
                    Thông tin vụ án
                 </div>
                 <div className="w-6 h-px bg-border mx-1"></div>
                 <div className="flex items-center gap-2 text-primary">
                    <div className="w-4 h-4 rounded-full bg-primary flex items-center justify-center text-white text-[10px] font-bold">2</div>
                    Diễn biến phiên tòa
                 </div>
                 <div className="w-6 h-px bg-border mx-1"></div>
                 <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full bg-muted text-muted-foreground flex items-center justify-center text-[10px] font-bold">3</div>
                    Nhận định & căn cứ
                 </div>
                 <div className="w-6 h-px bg-border mx-1"></div>
                 <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full bg-muted text-muted-foreground flex items-center justify-center text-[10px] font-bold">4</div>
                    Quyết định dự thảo
                 </div>
              </div>
           </div>

           <div className="flex items-center gap-3">
              <Button variant="outline" size="sm" className="h-9 gap-2 border-border text-foreground hover:bg-muted font-medium">
                Xuất Word <FileDown className="w-4 h-4 text-blue-500" />
              </Button>
              <Button variant="outline" size="sm" className="h-9 gap-2 border-border text-foreground hover:bg-muted font-medium">
                Xuất PDF <FileDown className="w-4 h-4 text-red-500" />
              </Button>
              <Button size="sm" className="h-9 gap-2 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 font-semibold ml-2">
                Mở đầy đủ <Maximize2 className="w-3.5 h-3.5" />
              </Button>
              <Button variant="ghost" size="icon" className="h-9 w-9 text-muted-foreground ml-2 hover:bg-muted hover:text-foreground">
                <X className="w-5 h-5" />
              </Button>
           </div>
        </div>
      </div>
    </div>
  );
}
