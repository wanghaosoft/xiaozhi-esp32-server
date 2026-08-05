package xiaozhi.modules.device.dto;

import java.math.BigDecimal;
import java.util.Map;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ExternalLiveEventRecordDTO {
    private String source;

    @NotBlank(message = "recordId 不能为空")
    private String recordId;

    private String roomId;
    private String roomTitle;

    @NotBlank(message = "eventType 不能为空")
    private String eventType;

    private String priority;
    private String actorId;
    private String actorName;
    private String content;
    private BigDecimal liveHeat;
    private Map<String, Object> normalizedPayload;
    private Map<String, Object> rawPayload;
    private String eventCreatedAt;
}