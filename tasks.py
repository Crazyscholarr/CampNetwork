# Danh sách các nhiệm vụ sẽ được thực hiện
TASKS = ["CRUSTY_SWAP"]

### LOYALTY CHỈ HOẠT ĐỘNG VỚI PROXY TĨNH!!! BẠN CÓ THỂ DÙNG RESIDENTIAL NHƯNG KHÔNG ĐƯỢC XOAY IP ###
### LOYALTY CHỈ HOẠT ĐỘNG VỚI PROXY TĨNH!!! BẠN CÓ THỂ DÙNG RESIDENTIAL NHƯNG KHÔNG ĐƯỢC XOAY IP ###
### LOYALTY CHỈ HOẠT ĐỘNG VỚI PROXY TĨNH!!! BẠN CÓ THỂ DÙNG RESIDENTIAL NHƯNG KHÔNG ĐƯỢC XOAY IP ### 

# Nhiệm vụ CRUSTY_SWAP gồm các module sau
CRUSTY_SWAP = [
    # "cex_withdrawal",  # Rút ETH từ sàn CEX (okx, bitget)
    "crusty_refuel",     # Nạp CAMP tại https://www.crustyswap.com/
    # "crusty_refuel_from_one_to_all",  # Nạp CAMP từ một ví đến tất cả ví tại https://www.crustyswap.com/
]

# Nhiệm vụ Loyalty trên Camp Network
CAMP_LOYALTY = [
    "camp_loyalty_connect_socials",      # Kết nối mạng xã hội
    "camp_loyalty_set_display_name",     # Đặt tên hiển thị
    "camp_loyalty_complete_quests",      # Hoàn thành nhiệm vụ
]

# CHỈ LÀ VÍ DỤ, HÃY TỰ TẠO NHIỆM VỤ RIÊNG CỦA BẠN
FULL_TASK = [
    "faucet",                            # Nhận token từ faucet
    "camp_loyalty_connect_socials",
    "camp_loyalty_set_display_name",
    "camp_loyalty_complete_quests",
]

SKIP = ["skip"]                          # Bỏ qua nhiệm vụ (dùng cho random hoặc kiểm tra log)

FAUCET = ["faucet"]                      # Nhận token từ faucet

CAMP_LOYALTY_CONNECT_SOCIALS = ["camp_loyalty_connect_socials"]           # Kết nối mạng xã hội
CAMP_LOYALTY_SET_DISPLAY_NAME = ["camp_loyalty_set_display_name"]         # Đặt tên hiển thị
CAMP_LOYALTY_COMPLETE_QUESTS = ["camp_loyalty_complete_quests"]           # Hoàn thành nhiệm vụ

# CÁC CHIẾN DỊCH LOYALTY
CAMP_LOYALTY_STORYCHAIN = ["camp_loyalty_storychain"]                     # StoryChain
CAMP_LOYALTY_TOKEN_TAILS = ["camp_loyalty_token_tails"]                   # Token Tails
CAMP_LOYALTY_AWANA = ["camp_loyalty_awana"]                               # AWANA
CAMP_LOYALTY_PICTOGRAPHS = ["camp_loyalty_pictographs"]                   # Pictographs
CAMP_LOYALTY_HITMAKR = ["camp_loyalty_hitmakr"]                           # Hitmakr
CAMP_LOYALTY_PANENKA = ["camp_loyalty_panenka"]                           # Panenka
CAMP_LOYALTY_SCOREPLAY = ["camp_loyalty_scoreplay"]                       # Scoreplay
CAMP_LOYALTY_WIDE_WORLDS = ["camp_loyalty_wide_worlds"]                   # Wide Worlds
CAMP_LOYALTY_ENTERTAINM = ["camp_loyalty_entertainm"]                     # EntertainM
CAMP_LOYALTY_REWARDED_TV = ["camp_loyalty_rewarded_tv"]                   # RewardedTV
CAMP_LOYALTY_SPORTING_CRISTAL = ["camp_loyalty_sporting_cristal"]         # Sporting Cristal
CAMP_LOYALTY_BELGRANO = ["camp_loyalty_belgrano"]                         # Belgrano
CAMP_LOYALTY_ARCOIN = ["camp_loyalty_arcoin"]                             # ARCOIN
CAMP_LOYALTY_KRAFT = ["camp_loyalty_kraft"]                               # Kraft
CAMP_LOYALTY_SUMMITX = ["camp_loyalty_summitx"]                           # SummitX
CAMP_LOYALTY_PIXUDI = ["camp_loyalty_pixudi"]                             # Pixudi
CAMP_LOYALTY_CLUSTERS = ["camp_loyalty_clusters"]                         # Clusters
CAMP_LOYALTY_JUKEBLOX = ["camp_loyalty_jukeblox"]                         # JukeBlox
CAMP_LOYALTY_CAMP_NETWORK = ["camp_loyalty_camp_network"]                 # Camp Network

"""
VI:
Bạn có thể tự tạo nhiệm vụ với các module bạn cần 
và thêm vào danh sách TASKS hoặc dùng các nhiệm vụ mẫu có sẵn.

( ) - Tất cả các module trong ngoặc tròn sẽ được thực hiện theo thứ tự ngẫu nhiên
[ ] - Chỉ một module trong ngoặc vuông sẽ được thực hiện ngẫu nhiên
XEM VÍ DỤ DƯỚI ĐÂY:

--------------------------------
!!! QUAN TRỌNG !!!
VÍ DỤ:

TASKS = [
    "CREATE_YOUR_OWN_TASK",
]
CREATE_YOUR_OWN_TASK = [
    "faucet",
    ("camp_loyalty_entertainm", "camp_loyalty_connect_socials"),
    ["camp_loyalty_awana", "camp_loyalty_camp_network"],
    "camp_loyalty_jukeblox",
]
--------------------------------

BÊN DƯỚI LÀ CÁC NHIỆM VỤ MẪU BẠN CÓ THỂ SỬ DỤNG:

--- TẤT CẢ NHIỆM VỤ ---

faucet - Nhận token từ Faucet trên Camp Network - https://faucet.campnetwork.xyz/

*** LOYALTY ***
camp_loyalty_connect_socials - Kết nối mạng xã hội trên Loyalty - https://loyalty.campnetwork.xyz/loyalty?editProfile=1&modalTab=social
camp_loyalty_set_display_name - Đặt tên hiển thị trên Loyalty - https://loyalty.campnetwork.xyz/loyalty?editProfile=1&modalTab=displayName
camp_loyalty_complete_quests - Hoàn thành nhiệm vụ trên Loyalty - https://loyalty.campnetwork.xyz/loyalty?editProfile=1&modalTab=quests

*** CÁC CHIẾN DỊCH LOYALTY ***
camp_loyalty_storychain - StoryChain
camp_loyalty_token_tails - Token Tails
camp_loyalty_awana - AWANA
camp_loyalty_pictographs - Pictographs
camp_loyalty_hitmakr - Hitmakr
camp_loyalty_panenka - Panenka
camp_loyalty_scoreplay - Scoreplay
camp_loyalty_wide_worlds - Wide Worlds
camp_loyalty_entertainm - EntertainM
camp_loyalty_rewarded_tv - RewardedTV
camp_loyalty_sporting_cristal - Sporting Cristal
camp_loyalty_belgrano - Belgrano
camp_loyalty_arcoin - ARCOIN
camp_loyalty_kraft - Kraft
camp_loyalty_summitx - SummitX
camp_loyalty_pixudi - Pixudi
camp_loyalty_clusters - Clusters
camp_loyalty_jukeblox - JukeBlox
camp_loyalty_camp_network - Camp Network

crusty_refuel - Nạp CAMP tại https://www.crustyswap.com/
crusty_refuel_from_one_to_all - Nạp CAMP từ một ví đến tất cả ví tại https://www.crustyswap.com/
cex_withdrawal - Rút ETH từ sàn CEX (okx, bitget)

KHÁC
skip - Bỏ qua nhiệm vụ (dùng cho random hoặc kiểm tra log)
"""
